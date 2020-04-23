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
class Humidity(Fact):
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

###################### RULE-BASED SYSTEM #####################
##############################################################
class ControlExpertSystem(KnowledgeEngine):
    expertalSystem = ExpertalSystemResult()

    def get_results(self):
        return self.expertalSystem.get_results()

    @Rule(AND(
        Time(time=P(lambda x: x > 16))
        ,Lights(light=False)
        ,Humans(humans=True)
    ))
    def _idx1(self):
        self.expertalSystem.add(key='lights', value='on')

    @Rule(AND(
        Time(time=P(lambda x: x > 16))
        ,Lights(light=True)
        ,Humans(humans=False)
    ))
    def _idx2(self):
        self.expertalSystem.add(key='lights', value='off')

    @Rule(AND(
        Time(time=P(lambda x: x < 16))
        ,Lights(light=True)
        ,Humans(humans=False)
    ))
    def _idx3(self):
        self.expertalSystem.add(key='lights', value='off')



    @Rule(AND(
        Windows(windows=False)
        ,Climate(climate=False)
        ,Temperature(temperature=P(lambda x: x > 26))
    ))
    def _idx3(self):
        self.expertalSystem.add(key='climate', value='on')
    @Rule(AND(
        Windows(windows=False)
        ,Climate(climate=False)
        ,Temperature(temperature=P(lambda x: x < 26))
    ))
    def _idx3(self):
        self.expertalSystem.add(key='climate', value='off')
    

class StartSystem():
    def __init__(self, temp, hum, motion, lights, gas, fire, climate):
        self.time = datetime.now().strftime("%H")
        self.lights = lights
        self.temp = temp
        self.hum = temp
        self.motion = motion
        self.gas = gas
        self.fire = fire
        self.climate = climate
    
    def getResult(self):
        engine = ControlExpertSystem()
        engine.reset()
        engine.declare(Time(time=18), Lights(light=self.lights), Humans(humans=self.motion), Gas(gas=self.gas), Fire(fire=self.fire), Climate(climate=self.climate))
        engine.run()
        return engine.get_results()

a = StartSystem(temp=21, hum=80, motion=False, lights=True).getResult()

print('result: ',a)