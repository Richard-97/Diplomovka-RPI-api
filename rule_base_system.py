from experta import *
from datetime import datetime

##################### DEFINE FACTS #####################
########################################################
class Climate(Fact):
    pass
class Time(Fact):
    pass
class Lights(Fact):
    pass
class Windows(Fact):
    pass
class Humans(Fact):
    pass
class Temperature(Fact):
    pass
class Gas(Fact):
    pass
class Fire(Fact):
    pass
class Alarm(Fact):
    pass
###################### RESULTS #########################
########################################################
class ExpertalSystemResult:
    def __init__(self):
        self.dictionary = {}

    def add(self, key, value):
        self.dictionary.update({key: value})

    def get_results(self):
        return self.dictionary
    
    def resetDict(self):
        self.dictionary.clear()
        print(self.dictionary)
        
###################### RULE-BASED SYSTEM #####################
##############################################################
class ControlExpertSystem(KnowledgeEngine):
    expertalSystem = ExpertalSystemResult()

    def get_results(self):
        return self.expertalSystem.get_results()

    def resetDict(self):
        self.expertalSystem.resetDict()
        
    @Rule(AND(
        Windows(windows=False)
        ,Gas(gas=True)
        ,Alarm(alarm=False)
    ))
    def _idx1(self):
        self.expertalSystem.add(key='alarm', value='on')
        self.expertalSystem.add(key='windows', value='on')
    
    @Rule(AND(
        Windows(windows=True)
        ,Gas(gas=True)
        ,Alarm(alarm=False)
    ))
    def _idx2(self):
        self.expertalSystem.add(key='alarm', value='on')
    
    @Rule(AND(
        Windows(windows=False)
        ,Fire(fire=True)
        ,Alarm(alarm=False)
    ))
    def _idx3(self):
        self.expertalSystem.add(key='alarm', value='on')
        self.expertalSystem.add(key='windows', value='on')
        
    @Rule(AND(
        Windows(windows=True)
        ,Fire(fire=True)
        ,Alarm(alarm=False)
    ))
    def _idx4(self):
        self.expertalSystem.add(key='alarm', value='on')
        
    @Rule(AND(
        Time(time=P(lambda x: x > 16))
        ,Lights(light=False)
        ,Humans(humans=True)
    ))
    def _idx5(self):
        self.expertalSystem.add(key='lights', value='on')

    @Rule(AND(
        Time(time=P(lambda x: x > 16))
        ,Lights(light=True)
        ,Humans(humans=False)
    ))
    def _idx6(self):
        self.expertalSystem.add(key='lights', value='off')

    @Rule(AND(
        Time(time=P(lambda x: x < 16))
        ,Lights(light=True)
        ,Humans(humans=False)
    ))
    def _idx7(self):
        self.expertalSystem.add(key='lights', value='off')


    @Rule(AND(
        Windows(windows=False)
        ,Climate(climate=False)
        ,Temperature(temperature=P(lambda x: x > 27))
    ))
    def _idx9(self):
        self.expertalSystem.add(key='windows', value='on')
    @Rule(AND(
        Windows(windows=False)
        ,Climate(climate=True)
        ,Temperature(temperature=P(lambda x: x < 27))
    ))
    def _idx10(self):
        self.expertalSystem.add(key='windows', value='off')
        
    @Rule(AND(
        Windows(windows=True)
        ,Climate(climate=True)
    ))
    def _idx11(self):
        self.expertalSystem.add(key='windows', value='off')

class StartSystem():
    def __init__(self, temp, motion, lights, gas, fire, climate, windows, alarm):
        self.time = int(datetime.now().strftime("%H"))
        self.lights = lights
        self.windows = windows
        self.temp = temp
        self.motion = motion
        self.gas = gas
        self.fire = fire
        self.climate = climate
        self.alarm = alarm
         
    def getResult(self):
        engine = ControlExpertSystem()
        engine.reset()
        engine.resetDict()
        engine.declare(Time(time=self.time),
                       Temperature(temperature=self.temp),
                       Lights(light=self.lights),
                       Humans(humans=self.motion),
                       Gas(gas=self.gas),
                       Fire(fire=self.fire),
                       Climate(climate=self.climate),
                       Windows(windows=self.windows),
                       Alarm(alarm=self.alarm)
                       )
        engine.run()
        data = engine.get_results()
        return data

#a = StartSystem(temp=21, hum=80, motion=False, lights=True).getResult()
