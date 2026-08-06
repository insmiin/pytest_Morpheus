from dataclasses import dataclass




def abc():
    @dataclass
    class ModuleType:
        GbRule: bool = False
        GbRule_GbRule: bool = False
        GbRule_Egon: bool = False
        GbFeature: bool = False
        unknown: bool = False

    m = ModuleType(GbRule=True)
    print(m)

    def xyz():
        mm = ModuleType(GbFeature=True)
        print(mm)



abc()

