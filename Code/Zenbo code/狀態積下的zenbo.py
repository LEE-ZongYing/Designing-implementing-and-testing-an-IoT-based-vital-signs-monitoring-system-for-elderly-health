import threading
import pyzenbo
from pyzenbo.modules.dialog_system import RobotFace
from pyzenbo.modules.error_code import code_to_description
import zmq
import time

# setting 
zenbo_speakSpeed = 100
zenbo_speakPitch = 100
zenbo_speakLanguage = 150
host = '192.168.0.4'
sdk = pyzenbo.connect(host)
domain = 'E7AABB554ACB414C9AB9BF45E7FA8AD9'
timeout = 15
is_looping = True
greeting={}
recommandation={}#0:'請問是要量測數據還是想查看網頁呢'
counter=0
#connection with server
context=zmq.Context()
socket=context.socket(zmq.PULL)
socket.bind("tcp://192.168.0.3:5556")
pusher = context.socket(zmq.PUSH)
pusher.bind("tcp://192.168.0.3:5557")



    
def on_state_change(serial, cmd, error, state):#Called when command state change in waiting queue
    msg = 'on_state_change serial:{}, cmd:{}, error:{}, state:{}'
    print(msg.format(serial, cmd, error, state))
    if error:
        print('on_state_change error:', code_to_description(error))

def on_result(**kwargs):# Called when a robot command sending result.
    print('on_result', kwargs)


def on_vision(*args):#Called when vision service sending result.
    print('on_vision', args)
    if not event_vision.isSet():
        event_vision.set()


def listen_callback(args):
    print('callbackS')
    slu = args.get('event_slu_query', None)
    if slu and '量測指標'==str(slu.get('app_semantic').get('originalSentence')) :
        print(slu)
        def job():
            sdk.robot.set_expression(RobotFace.HAPPY)
            sdk.robot.set_expression(RobotFace.DEFAULT,'好的，那請您前往量測儀器進行測量哦', {'speed':zenbo_speakSpeed, 'pitch':zenbo_speakPitch, 'languageId':zenbo_speakLanguage} , sync = True)
        t = threading.Thread(target=job)
        t.start()
        if not event_listen.isSet():
            event_listen.set()
            #此時使用者會插入健保卡、State become CardOnly from initialState
    elif slu and '查看資料'==str(slu.get('app_semantic').get('originalSentence')) :
        print(slu)
        def job():
            sdk.robot.set_expression(RobotFace.HAPPY)
            sdk.robot.set_expression(RobotFace.DEFAULT,'這是您的QRCode', {'speed':zenbo_speakSpeed, 'pitch':zenbo_speakPitch, 'languageId':zenbo_speakLanguage} , sync = True)
            #螢幕跳出QRcode
        t = threading.Thread(target=job)
        t.start()
        t.join()


def say_hello_and_ask(self):
    print('say_hello_and_ask')
    sdk.robot.set_expression(RobotFace.HAPPY, timeout=5)
    sdk.robot.jump_to_plan(domain, 'lanuchHelloWolrd_Plan')
    SirOrMama=['先生','女士']
    flag=1 if self.unit=='MM' else 0#server幫我篩選過，故比較沒那些難寫   
    sdk.robot.speak_and_listen(self.MeasureValue+SirOrMama[flag]+'你好,我是 Zenbo Junior，請問您想量測指標或是查看歷史資料呢?')
    #需要量測身體狀況，請插入健保卡以便搜尋您的歷史資料哦


def voice():
    print(counter)
    sdk.robot.set_expression(RobotFace.DEFAULT,greeting[counter],{'speed':zenbo_speakSpeed,'pitch':zenbo_speakPitch, 'languageId':zenbo_speakLanguage})
    zenbo.robot.register_listen_callback(1207, listen_callback)
    time.sleep(int(2))  

def not_found():
    print('not_found')
    sdk.robot.set_expression(RobotFace.HAPPY)
    #sdk.robot.set_expression(RobotFace.DEFAULT, 'Hello,我是Zenbo照護機器人,能夠檢測您目前的健康狀況哦', {'speed':zenbo_speakSpeed, 'pitch':zenbo_speakPitch, 'languageId':zenbo_speakLanguage} , sync = True)
    sdk.robot.set_expression(RobotFace.TIRED, timeout=5)

class Switcher(object):#state switcher 
    def __init__(self,ATN,MeasureValue,unit):
        self.method_name='number_'+str(ATN)
        self.method=self.getattr(self, method_name,'NO')
        self.ATN=ATN
        self.MeasureValue=MeasureValue
        self.unit=unit
        return self.method_name
    def number_0(self):#初始狀態，無限開啟人臉辨識就打招呼
        result = sdk.vision.request_detect_face(enable_debug_preview=True, timeout=50)
        print(result)
        is_detect_face = event_vision.wait(timeout)
        sdk.vision.cancel_detect_face()
        if is_detect_face:
            sdk.robot.set_expression(RobotFace.DEFAULT,'您好，我是您的健康監控小幫手Zenbo，對健康有疑問都能夠來找我喔',{'speed':zenbo_speakSpeed,'pitch':zenbo_speakPitch, 'languageId':zenbo_speakLanguage})
            #被直接詢問專業知識
            pusher.send_string("yes")
    def number_8(self):#onlyCard
        #ask measure or check web語音辨識
        say_hello_and_ask(self)#->問候後會自己聽
        is_get_listening = event_listen.wait(timeout)#timeout內有聽到不用謝謝則回覆...，
        if is_get_listening:
            print('有人要量測數據')
            event_listen.clear()
            event_vision.clear()
        elif is_get_listening==0:
            print('不用謝謝or沒人or叫出網頁or沒有語音辨識到，但有卡片')
        pusher.send_string("yes")
        # print('counter = {} '.format(counter))
    def number_9(self):#Card+pressure
        recommandation[self.ATN]=''
        systolicBP=(String[0:int(half)-2])
        DiastolicBP=String[int(half)-1:length-4]
        greeting[counter]='以偵測到血壓訊號，目前收縮壓為'+String[0:int(half)-2]+'mmhg、擴張壓為'+String[int(half)-1:length-4]+'mmhg'+'心跳每分鐘'+String[xx]+'下'
        SPH=True if systolicBP>140 else False
        DPH=True if DiastolicBP>90 else False
        if SPH==False:
            if DPH:
                recommandation[self.ATN]='目前舒張壓偏高喔，若有任何問題歡迎在量測一次，建議能左右手血壓各量測一次，分析結果會更為準確喔'
            else:
                {
                    recommandation[self.ATN]='恭喜你還非常的健康喔，保持目前的生活作息，能使你更有活力喔。'
                }
        else:{
            if DPH:
                recommandation[self.ATN]='收縮血壓、擴張血壓數據偏高，勞煩您近期多注意自己的身體，若出現頭暈、噁心、嘔吐現象請馬上前往醫院進行檢查'
        }
        recommandation+='請繼續量測體溫、體重以便讓Zenbo Junior繼續替您做更詳細的健康分析哦'
        print(recommandation[counter])
    def number_12(self):#Card+temperature
        recommandation[self.ATN]=''
        greeting[self.ATN]='以偵測到體溫訊號，目前體溫為'+str(self.MeasureValue)+'度,請繼續量測體重、血壓以便讓AI替您做健康分析唷'
        flag = True if RealNumber>38.0 else False :
        if flag:
            recommandation[self.ATN]='您的體溫過高瞜，為了您以及Zenbo的健康請一同戴上口罩八，此外如果身體有任何不適請盡速前往醫院'
        else:
            if RealNumber>37.0:
                recommandation[self.ATN]='體溫稍高，若有運動、跑跳皆為正常現象，想再次確認體溫，歡迎過1至2分鐘後，再次回來做量測'
        print(recommandation[self.ATN])#CheckPoint
    def number_10(self):#Card+weight
        recommandation[self.ATN]='以偵測到體重訊號，目前體重為'+self.MeasureValue+'公斤,請繼續量測體溫、血壓，以便讓AI替您做健康分析唷'
        recommandation[self.ATN]+='能提供Zenbo您的身高嗎? Zenbo能依照身高、體重來建議您如何維持健康哦'
        #如何讓user提供身高
        print(recommandation[self.ATN])
    #-------------------1 phase and 2 phase 分隔線
    def number_11(self):#Card Weight Pressure
        #使用者至第二步，故想查看整體述職的分析結果，說出數值並請使用者測量完。
    def ChangeState(self,NewATN)
        if NewATN == self.ATN:
            self.method_name='number_'+str(ATN)
            self.method=self.getattr(self, method_name,'NO')
            
        recommandation[self.ATN]='以量測到....訊號，數值為:'+str(self.ATN)+'請前往量測下一生理指標。'
    def number_13(self):# Card Temperature + Pressure
        recommandation[self.ATN]='以量測到....訊號，數值為:'+str(self.ATN)+'請前往量測下一生理指標。'
    def number_14():# Card Temperature +Weight
        recommandation[self.ATN]='以量測到....訊號，數值為:'+str(self.ATN)+'請前往量測下一生理指標。'
    def FinishState(self):
        #秀出網頁+QRcode
        #Zenbo : 這邊是您此次量測數值的紀錄，想查看歷史量測資料皆可以以手機掃描下方QRcode，by the way 每次AI數值分析建議、結果也會一併放置在網頁上喔。
class number_0(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):
class number_8(number_0):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):
class number_9(number_8):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):
class number_12(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):
class number_10(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):          
class number_0(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):
    # @property
    # def s(self, )
    
    # def get_value(self,)

    # def send(self, unit):
    #     pass
class number_0(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):    
class number_0(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):    
class number_0(object):#全0時初始狀態
    def __init__(self,obj1):
        obj1.method
    def exit(self):    


def run():
    RawData=socket.recv().decode('utf-8')
    Case=Switcher((lambda x:x[0:2])(RawData),(lambda x:x[2:len(x)-2])(RawData),(lambda x:x[len(x)-2:len(x)])(RawData))
    print(Case)#CheckPoint
    cas.exec()
    Is_Card_Input=event_cardinput.wait(timeout)
    CardThread=threading.Thread(target=voice)
    CardThread.start()
    CardThread.join()
    pusher.send_string("yes")
    print('counter = {} '.format(counter))

class StateManager(object):
    def ChangeState(self,NewATN,obj)
        if NewATN == obj.ATN:
            self.method=


try:
    while is_looping:
            CardThread=threading.Thread(target=voice)
            CardThread.start()
            CardThread.join()
            pusher.send_string("yes")
            print('counter = {} '.format(counter))
            while Is_Card_Input and counter!=100: 
                HealthIndicator=socket.recv().decode('utf-8')
                CheckDevise(HealthIndicator)
                exec()
                print('counter = {} '.format(counter))
            event_cardinput.clear()
        else:
            not_found()
        sdk.robot.set_expression(RobotFace.HIDEFACE, timeout=5)
finally:
    sdk.robot.stop_speak_and_listen()
    sdk.vision.cancel_detect_face()
    sdk.release()

event_cardinput=threading.Event()
event_vision = threading.Event()
event_listen = threading.Event()
sdk.on_state_change_callback = on_state_change
sdk.on_result_callback = on_result
sdk.on_vision_callback = on_vision
sdk.robot.register_listen_callback(domain, listen_callback)
sdk.robot.set_expression(RobotFace.HIDEFACE, timeout=5)