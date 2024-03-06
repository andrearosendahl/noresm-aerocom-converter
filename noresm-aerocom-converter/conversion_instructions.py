from enum import Enum
from typing import Callable, Optional
from xarray import Dataset
import re
from functools import partial
import yaml

class Instruction:
    TOTAL_FAC = "([+-]?[0-9]*[.]?[0-9]+)\*\((.*)\)"

    def __init__(self) -> None: ...

    @classmethod
    def get_instruction(cls, instruction: str):
        return cls._parse_instruction(cls, instruction)

    def _parse_instruction(self, instruction: str):
        total_fac = None
        instructions = ""
        total_fac_expr = re.findall(self.TOTAL_FAC, instruction)

        if len(total_fac_expr) == 1:
            if len(total_fac_expr[0]) == 2:
                total_fac = float(total_fac_expr[0][0])
                instruction = total_fac_expr[0][1]
            else:
                raise ValueError(f"Something wrong with total factori in {instruction}")

        insts = instruction.split("+")
        for ins in insts:
            fac = ins.split("*")

            if len(fac) == 2:
                if instructions == "":
                    instructions += f"{fac[0]}*x.{fac[1]}"
                else:
                    instructions += f"+{fac[0]}*x.{fac[1]}"
            elif len(fac) == 1:
                if instructions == "":
                    instructions += f"x.{fac[0]}"
                else:
                    instructions += f"+x.{fac[0]}"
            else:
                raise ValueError(
                    f"Something wrong with instrunction {ins} in {instruction}"
                )

        if total_fac is not None:
            instructions = f"{total_fac}*({instructions})"

        return instructions


LEVEL = dict(
    M="ModelLevel",
    S="Surface",
    C="Column",
    SS="SurfaceAtStations",
    MS="ModelLevelAtStations",
    default="INVALIDCOORDINATETYPE",
)


# LL = 31

FREQUENCY = "monthly"
# converts from sulfuric acid (H2SO4) to SO4 (96/98 MW)
SF1 = 0.9796
# converts from ammonium sulfate (NH4_2SO4) to SO4 (96/134 MW)
SF2 = 0.7273
# mass fraction of DST_A3 for d>10 um (from AeroTab, assuming no growth))
F10DSTA3 = 0.23
# mass fraction of SS_A3 for d>10 um (from AeroTab, assuming no growth))
F10SSA3 = 0.008
# RAIR
RAIR = 287.0


def get_conversion_intstructions(LL: str, yaml_file: Optional[str] = None ) -> dict[str, dict[str, str]]:
    ARRAY = [
        f"area&GRIDAREA&m2&S",
        f"landf&LANDFRAC&1&S",
        f"ps&PS&Pa&S",
        f"od550csaer&CDOD550/(CLDFREE+0.0004)&1&C",
        f"od550aer&DOD550&1&C",
        f"od440aer&DOD440&1&C",
        f"od870aer&DOD870&1&C",
        f"abs550aer&ABS550AL&1&C",
        f"abs550bc&A550_BC&1&C",
        f"abs550dust&A550_DU&1&C",
        f"abs550oa&A550_POM&1&C",
        f"abs550ss&A550_SS&1&C",
        f"od550so4&D550_SO4&1&C",
        f"od550bc&D550_BC&1&C",
        f"od550oa&D550_POM&1&C",
        f"od550ss&D550_SS&1&C",
        f"od550dust&D550_DU&1&C",
        f"od550dustDSTA2&D550_DUA2&1&C",
        f"od550dustDSTA3&D550_DUA3&1&C",
        f"od440dust&D440_DU&1&C",
        f"od440dustDSTA2&D440_DUA2&1&C",
        f"od440dustDSTA3&D440_DUA3&1&C",
        f"od870dust&D870_DU&1&C",
        f"od870dustDSTA2&D870_DUA2&1&C",
        f"od870dustDSTA3&D870_DUA3&1&C",
        f"od10umdust&DOD10UM&1&C",
        f"od10umdustDSTA2&DOD10UMA2&1&C",
        f"od10umdustDSTA3&DOD10UMA3&1&C",
        f"od550lt1dust&DLT_DUST&1&C",
        f"od550lt1aer&DLT_SS+DLT_DUST+DLT_SO4+DLT_BC+DLT_POM&1&C",
        f"od550gt1aer&DOD550-DLT_SS-DLT_DUST-DLT_SO4-DLT_BC-DLT_POM&1&C",
        f"od550aerh2o&DOD550-OD550DRY&1&C",
        f"emidust&SFDST_A2+SFDST_A3&kg m-2 s-1&S",
        f"emidustDSTA2&SFDST_A2&kg m-2 s-1&S",
        f"emidustDSTA3&SFDST_A3&kg m-2 s-1&S",
        f"wetdust&-1.0*(DST_A2SFWET+DST_A3SFWET+DST_A2_OCWSFWET+DST_A3_OCWSFWET)&kg m-2 s-1&S",
        f"wetdustDSTA2&-1.0*(DST_A2SFWET+DST_A2_OCWSFWET)&kg m-2 s-1&S",
        f"wetdustDSTA3&-1.0*(DST_A3SFWET+DST_A3_OCWSFWET)&kg m-2 s-1&S",
        f"drydust&-1.0*(DST_A2DDF+DST_A3DDF+DST_A2_OCWDDF+DST_A3_OCWDDF)&kg m-2 s-1&S",
        f"drydustDSTA2&-1.0*(DST_A2DDF+DST_A2_OCWDDF)&kg m-2 s-1&S",
        f"drydustDSTA3&-1.0*(DST_A3DDF+DST_A3_OCWDDF)&kg m-2 s-1&S",
        f"loadoa&cb_OM+cb_OM_NI_OCW+cb_OM_AI_OCW+cb_OM_AC_OCW+cb_SOA_NA_OCW+cb_SOA_A1_OCW&kg m-2&C",
        f"loadbc&cb_BC+cb_BC_NI_OCW+cb_BC_N_OCW+cb_BC_A_OCW+cb_BC_AI_OCW+cb_BC_AC_OCW&kg m-2&C",
        f"loadss&cb_SALT+cb_SS_A1_OCW+cb_SS_A2_OCW+cb_SS_A3_OCW&kg m-2&C",
        f"loaddu&cb_DUST+cb_DST_A2_OCW+cb_DST_A3_OCW&kg m-2&C",
        f"loadduDSTA2&cb_DST_A2+cb_DST_A2_OCW&kg m-2&C",
        f"loadduDSTA3&cb_DST_A3+cb_DST_A3_OCW&kg m-2&C",
        f"loadso2&cb_SO2&kg m-2&C",
        f"loadso4&{SF1}*(cb_SO4_A1+{SF2}/{SF1}*cb_SO4_A2+cb_SO4_NA+cb_SO4_PR+cb_SO4_AC+cb_SO4_A1_OCW+{SF2}/{SF1}*cb_SO4_A2_OCW+cb_SO4_AC_OCW+cb_SO4_NA_OCW+cb_SO4_PR_OCW)&kg m-2&C",
        f"loaddms&cb_DMS&kg m-2&C",
        f"clt&CLDTOT&1&C",
        f"cldlow&CLDLOW&1&C",
        f"cldmid&CLDMED&1&C",
        f"cldhigh&CLDHGH&1&C",
        f"convclt&CNVCLD&1&C",
        f"lwp&TGCLDLWP&kg m-2&C",
        f"clivi&TGCLDIWP&kg m-2&C",
        f"rsdt&SOLIN&W m-2&S",
        f"rsds&FSDS&W m-2&S",
        f"rsdsDSTA2&FSDS_DSTA2&W m-2&S",
        f"rsdsDSTA3&FSDS_DSTA3&W m-2&S",
        f"rsut&FSUTOA&W m-2&S",
        f"rsus&FSDS-FSNS&W m-2&S",
        f"rsdscs&FSDSC&W m-2&S",
        f"rlutcs&FLUTC&W m-2&C",
        f"rlut&FLUT&W m-2&C",
        f"rlds&FLDS&W m-2&C",
        f"rlus&FLDS-FLNS&W m-2&C",
        f"rsutca&FSNT-FSNT_DRF&W m-2&C",
        f"rlutca&FLNT_DRF-FLNT&W m-2&C",
        f"rsutcsca&FSNT_DRF-FSNTCDRF&W m-2&C",
        f"rlutcsca&FLNTCDRF-FLNT_DRF&W m-2&C",
        f"rsutcaDSTA2&FSNT-FSNT_DSTA2&W m-2&C",
        f"rsutcaDSTA3&FSNT-FSNT_DSTA3&W m-2&C",
        f"rlutcaDSTA2&FLNT_DSTA2-FLNT&W m-2&C",
        f"rlutcaDSTA3&FLNT_DSTA3-FLNT&W m-2&C",
        f"rsutcscaDSTA2&FSNT_DSTA2-FSNTCDRF_DSTA2&W m-2&C",
        f"rsutcscaDSTA3&FSNT_DSTA3-FSNTCDRF_DSTA3&W m-2&C",
        f"orog&0.102*PHIS&m&S",
        f"pr&1000*PRECT&kg m-2 s-1&S",
        f"prsn&PRECSC+1000*PRECSL&kg m-2 s-1&S",
        f"temp&T&K&M",
        f"tos&SST&K&S",
        f"tas&TREFHT&K&S",
        f"ts&TS&K&S",
        f"tatp&TROP_T&K&C",
        f"ztp&TROP_Z&m&C",
        f"bldep&PBLH&m&C",
        f"prc&1000*PRECC&kg m-2 s-1&C",
        f"hus&Q&K&M",
        f"airmass&AIRMASS&kg m-2&M",
        f"abs550dryaer&ABSDRYAE&m-1&M",
        f"cl3D&CLOUD&1&M",
        f"ccn&CCN6&cm3&M",
        f"mmraerh2o&MMR_AH2O&kg kg-1&M",
        f"mmrso4&{SF1}*(SO4_A1+{SF2}/{SF1}*SO4_A2+SO4_AC+SO4_NA+SO4_PR+SO4_A1_OCW+{SF2}/{SF1}*SO4_A2_OCW+SO4_AC_OCW+SO4_NA_OCW+SO4_PR_OCW)&kg kg-1&M",
        f"mmroa&OM_AC+OM_AI+OM_NI+SOA_NA+SOA_A1+OM_AC_OCW+OM_AI_OCW+OM_NI_OCW+SOA_NA_OCW+SOA_A1_OCW&kg kg-1&M",
        f"mmrbc&BC_A+BC_AC+BC_AX+BC_N+BC_NI+BC_AI+BC_A_OCW+BC_AC_OCW+BC_N_OCW+BC_NI_OCW+BC_AI_OCW&kg kg-1&M",
        f"mmrss&SS_A1+SS_A2+SS_A3+SS_A1_OCW+SS_A2_OCW+SS_A3_OCW&kg kg-1&M",
        f"mmrdu&DST_A2+DST_A3+DST_A2_OCW+DST_A3_OCW&kg kg-1&M",
        f"ccn860[time,lat,lon]&(CCN6(:,25,:,:))&cm3&C",
        f"pressure[time,lev,lat,lon]&float(P0*hyam+PS*hybm)&Pa&M",
        f"rho[time,lev,lat,lon]&float(P0*hyam+PS*hybm)/({RAIR}*T(:,:,:,:))&kg m-3&M",
        f"sconcso4[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*{SF1}*(SO4_A1(:,{{LL}},:,:)+{SF2}/{SF1}*SO4_A2(:,{{LL}},:,:)+SO4_PR(:,{{LL}},:,:)+SO4_NA(:,{{LL}},:,:)+SO4_A1_OCW(:,{{LL}},:,:)+{SF2}/{SF1}*SO4_A2_OCW(:,{{LL}},:,:)+SO4_PR_OCW(:,{{LL}},:,:)+SO4_NA_OCW(:,{{LL}},:,:))*1.e9&ug m-3&S",
        f"sconcso2[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*SO2(:,{{LL}},:,:)*1.e9*64.066/28.97&ug m-3&S",
        f"sconcdms[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*DMS(:,{{LL}},:,:)*1.e9*62.13/28.97&ug m-3&S",
        f"sconcss[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*(SS_A1(:,{{LL}},:,:)+SS_A2(:,{{LL}},:,:)+SS_A3(:,{{LL}},:,:)+SS_A1_OCW(:,{{LL}},:,:)+SS_A2_OCW(:,{{LL}},:,:)+SS_A3_OCW(:,{{LL}},:,:))*1.e9&ug m-3&S",
        f"sconcdust[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*(DST_A2(:,{{LL}},:,:)+DST_A3(:,{{LL}},:,:)+DST_A2_OCW(:,{{LL}},:,:)+DST_A3_OCW(:,{{LL}},:,:))*1.e9&ug m-3&S",
        f"sconcdustpm25&C_MIPM25&ug m-3&S",
        f"sconcbc[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*(BC_A(:,{{LL}},:,:)+BC_AC(:,{{LL}},:,:)+BC_AX(:,{{LL}},:,:)+BC_N(:,{{LL}},:,:)+BC_NI(:,{{LL}},:,:)+BC_AI(:,{{LL}},:,:)+BC_A_OCW(:,{{LL}},:,:)+BC_AC_OCW(:,{{LL}},:,:)+BC_N_OCW(:,{{LL}},:,:)+BC_NI_OCW(:,{{LL}},:,:)+BC_AI_OCW(:,{{LL}},:,:))*1.e9&ug m-3&S",
        f"sconcoa[time,lat,lon]&(PS(:,:,:)/287.0/TS(:,:,:))*(OM_AC(:,{{LL}},:,:)+OM_AI(:,{{LL}},:,:) +OM_NI(:,{{LL}},:,:)+SOA_NA(:,{{LL}},:,:)+SOA_A1(:,{{LL}},:,:)+OM_AC_OCW(:,{{LL}},:,:)+OM_AI_OCW(:,{{LL}},:,:)+OM_NI_OCW(:,{{LL}},:,:)+SOA_NA_OCW(:,{{LL}},:,:)+SOA_A1_OCW(:,{{LL}},:,:))*1.e9&ug m-3&S",
        f"sconcpm25&PM25&ug m-3&S",
        f"sconcpm10[time,lat,lon]&PMTOT(:,:,:)-PS(:,:,:)/287.0/TS(:,:,:)*1.e9*({F10DSTA3}*DST_A3(:,{{LL}},:,:)+{F10SSA3}*SS_A3(:,{{LL}},:,:))&ug m-3&S",
        f"sconcpm10by20[time,lat,lon]&(PMTOT(:,:,:)-PS(:,:,:)/287.0/TS(:,:,:)*1.e9*({F10DSTA3}*DST_A3(:,{{LL}},:,:)+{F10SSA3}*SS_A3(:,{{LL}},:,:)))/(PMTOT(:,:,:))&1&S",
    ]
    if yaml_file is None:

        return _get_conversion_intstructions(ARRAY, LL)
    else:
        make_yaml(ARRAY, yaml_file)
        return 


def make_yaml(array: list[str], file: str) -> None:
    instructions = {}
    for line in array:
        #words = line.format(LL=LL).split("&")
        words = line.split("&")
        aerocom_name = words[0].split("[")[0]
        instructions[aerocom_name] = dict(
            new_name=words[0],
            formula=words[1],
            units=words[2],
            coordinates=LEVEL[words[3]] if words[3] in LEVEL else LEVEL["default"],
        )
    
    with open(file, "w") as f:
        yaml.safe_dump(instructions, f)

    




# AEROCOMNAME&CAMOSLONAME(OR FORMULA)&UNIT&CoordinateType
def _get_conversion_intstructions(
    array: list[str], LL: str
) -> dict[str, dict[str, str]]:
    instructions = {}
    for line in array:
        words = line.format(LL=LL).split("&")
        aerocom_name = words[0].split("[")[0]
        instructions[aerocom_name] = dict(
            new_name=words[0],
            formula=words[1],
            command=Instruction.get_instruction(words[1]),
            units=words[2],
            coordinates=LEVEL[words[3]] if words[3] in LEVEL else LEVEL["default"],
        )

    return instructions



if __name__ == "__main__":
    yaml_file = "./conversions_test.yaml"
    inst = get_conversion_intstructions(21, yaml_file)
    #breakpoint()
