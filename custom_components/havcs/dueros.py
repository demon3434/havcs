import json
import uuid
import time
import logging

from .util import decrypt_device_id, encrypt_device_id
from .helper import VoiceControlProcessor, VoiceControlDeviceManager
from .const import DATA_HAVCS_BIND_MANAGER, INTEGRATION, ATTR_DEVICE_ACTIONS

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)

DOMAIN = 'dueros'
LOGGER_NAME = 'dueros'

async def createHandler(hass, entry):
    mode = ['handler']
    return VoiceControlDueros(hass, mode, entry)

class PlatformParameter:
    device_attribute_map_h2p = {
        'temperature': 'temperatureReading',
        'targettemperature': 'targetTemperature',
        'brightness': 'brightness',
        'humidity': 'humidity',
        'targethumidity': 'humidity',
        'pm25': 'PM25',
        'pm10': 'PM10',
        'co2': 'ppm',
        'hcho': 'hcho',
        'turnonstate': 'turnOnState',
        'mode': 'mode',
        'havc_mode': 'havcmode',
        'percentage': 'fanspeed',
        'state': 'state',
    }
    
    device_action_map_h2p ={
        'turn_on': 'turnOn',   #鎵撳紑
        'turn_off': 'turnOff', #鍏抽棴
        'timing_turn_on': 'timingTurnOn',   #瀹氭椂鎵撳紑
        'timing_turn_off': 'timingTurnOff', #瀹氭椂鍏抽棴
        'increase_brightness': 'incrementBrightnessPercentage',  #璋冧寒鐏厜
        'decrease_brightness': 'decrementBrightnessPercentage',  #璋冩殫鐏厜
        'set_brightness': 'setBrightnessPercentage',             #璁剧疆鐏厜浜害
        'set_color': 'setColor',                                #璁剧疆棰滆壊
        'increase_temperature': 'incrementTemperature',         #鍗囬珮娓╁害
        'decrease_temperature': 'decrementTemperature',         #闄嶄綆娓╁害
        'set_temperature': 'setTemperature',                    #璁剧疆娓╁害
        'increase_speed': 'incrementFanSpeed',                  #澧炲姞椋庨€?        'decrease_speed': 'decrementFanSpeed',                  #鍑忓皬椋庨€?        'set_percentage': 'setFanSpeed',                        #璁剧疆椋庨€?       
        'pause': 'pause',                                       #鏆傚仠        
        'set_humidity': 'setHumidity',                          #璁剧疆婀垮害妯″紡       
        'set_hvac_mode': 'setMode',                             #璁剧疆妯″紡
        'set_oscillate': 'setMode',                         #璁剧疆妯″紡
        'unset_oscillate': 'unSetMode',                     #鍙栨秷璁剧疆鐨勬ā寮?        'volume_up': 'incrementVolume',                     #璋冮珮闊抽噺
        'volume_down': 'decrementVolume',                   #璋冧綆闊抽噺
        'volume_set': 'setVolume',                          #璁剧疆闊抽噺
        'volume_mute': 'setVolumeMute',                     #璁剧疆闈欓煶鐘舵€?        'tv_down': 'decrementTVChannel',                    #涓婁竴涓閬?        'tv_up': 'incrementTVChannel',                      #涓嬩竴涓閬?        'media_pause': 'pause',
        'media_play': 'continue',
        'query_temperature': 'getTemperatureReading',           #鏌ヨ褰撳墠娓╁害
        'query_humidity': 'getHumidity',                        #鏌ヨ婀垮害
        'query_targettemperature': 'getTargetTemperature',     #鏌ヨ鐩爣娓╁害
        'query_targethumidity': 'getTargetHumidity',           #鏌ヨ鐩爣婀垮害 
        'query_state': 'getState',                #鏌ヨ璁惧鎵€鏈夌姸鎬?        'query_pm25': 'getAirPM25',                    #鏌ヨPM2.5
        'query_pm10': 'getAirPM10',          #鏌ヨPM10
        'query_co2': 'getCO2Quantity',          #鏌ヨ浜屾哀鍖栫⒊鍚噺
        'query_aqi': 'getAirQualityIndex',      #鏌ヨ绌烘皵璐ㄩ噺
        'query_location': 'getLocation',        #鏌ヨ璁惧鎵€鍦ㄤ綅缃?        'query_turnonstate': 'getTurnOnState',    #鏌ヨ寮€鍏崇姸鎬?        'set_colortemperature': 'setColorTemperature' ,  #璁剧疆鐏厜鑹叉俯
        'increment_colortemperature': 'incrementColorTemperature' ,  #澧為珮鐏厜鑹叉俯
        'decrement_colortemperature': 'decrementColorTemperature' ,  #闄嶄綆鐏厜鑹叉俯
        # ' ': 'setPower' ,  #璁剧疆鍔熺巼
        # ' ': 'incrementPower' ,  #澧炲ぇ鍔熺巼
        # ' ': 'decrementPower' ,  #鍑忓皬鍔熺巼
        # ' ': 'setGear' ,  #璁剧疆妗ｄ綅
        # ' ': 'timingSetMode' ,  #瀹氭椂璁剧疆妯″紡
        # ' ': 'timingUnsetMode' ,  #瀹氭椂鍙栨秷璁剧疆鐨勬ā寮?        # ' ': 'setTVChannel' ,  #璁剧疆棰戦亾
        # ' ': 'returnTVChannel' ,  #杩斿洖涓婁釜棰戦亾
        # ' ': 'chargeTurnOn' ,  #寮€濮嬪厖鐢?        # ' ': 'chargeTurnOff' ,  #鍋滄鍏呯數
        # ' ': 'getOilCapacity' ,  #鏌ヨ娌归噺
        # ' ': 'getElectricityCapacity' ,  #鏌ヨ鐢甸噺
        # ' ': 'setLockState' ,  #涓婇攣/瑙ｉ攣
        # ' ': 'getLockState' ,  #鏌ヨ閿佺姸鎬?        # ' ': 'setSuction' ,  #璁剧疆鍚稿姏
        # ' ': 'setWaterLevel' ,  #璁剧疆姘撮噺
        # ' ': 'setCleaningLocation' ,  #璁剧疆娓呮壂浣嶇疆
        # ' ': 'setComplexActions' ,  #鎵ц鑷畾涔夊鏉傚姩浣?        # ' ': 'setDirection' ,  #璁剧疆绉诲姩鏂瑰悜
        # ' ': 'submitPrint' ,  #鎵撳嵃
        # 'increment_humidity': 'incrementHumidity',              #澧炲ぇ婀垮害
        # 'decrement_humidity': 'decrementHumidity',              #闄嶄綆婀垮害 
        # ' ': 'getWaterQuality' ,  #鏌ヨ姘磋川
        # ' ': 'getTimeLeft' ,  #鏌ヨ鍓╀綑鏃堕棿
        # ' ': 'getRunningStatus' ,  #鏌ヨ杩愯鐘舵€?        # ' ': 'getRunningTime' ,  #鏌ヨ杩愯鏃堕棿
        # ' ': 'setTimer' ,  #璁惧瀹氭椂
        # ' ': 'timingCancel' ,  #鍙栨秷璁惧瀹氭椂
        # ' ': 'reset' ,  #璁惧澶嶄綅
        # ' ': 'incrementHeight' ,  #鍗囬珮楂樺害
        # ' ': 'decrementHeight' ,  #闄嶄綆楂樺害
        # ' ': 'setSwingAngle' ,  #璁剧疆鎽嗛瑙掑害
        # ' ': 'getFanSpeed' ,  #鏌ヨ椋庨€?        # ' ': 'incrementMist' ,  #澧炲ぇ闆鹃噺
        # ' ': 'decrementMist' ,  #瑙佹晥闆鹃噺
        # ' ': 'setMist' ,  #璁剧疆闆鹃噺
        # ' ': 'startUp' ,  #璁惧鍚姩
        # ' ': 'setFloor' ,  #璁剧疆鐢垫妤煎眰
        # ' ': 'decrementFloor' ,  #鐢垫鎸変笅
        # ' ': 'incrementFloor' ,  #鐢垫鎸変笂
        # ' ': 'incrementSpeed' ,  #澧炲姞閫熷害
        # ' ': 'decrementSpeed' ,  #闄嶄綆閫熷害
        # ' ': 'setSpeed' ,  #璁剧疆閫熷害
        # ' ': 'getSpeed' ,  #鑾峰彇閫熷害
        # ' ': 'getMotionInfo' ,  #鑾峰彇璺戞淇℃伅
        # ' ': 'turnOnBurner' ,  #鎵撳紑鐏剁溂
        # ' ': 'turnOffBurner' ,  #鍏抽棴鐏剁溂
        # ' ': 'timingTurnOnBurner' ,  #瀹氭椂鎵撳紑鐏剁溂
        # ' ': 'timingTurnOffBurner' ,  #瀹氭椂鍏抽棴鐏剁溂
    }
    _device_type_alias = {
        "LIGHT": "light",
        "AIR_CONDITION": "air conditioner",
        "CURTAIN": "curtain",
        "CURT_SIMP": "curtain",
        "SOCKET": "socket",
        "SWITCH": "switch",
        "FRIDGE": "fridge",
        "WATER_PURIFIER": "water purifier",
        "HUMIDIFIER": "humidifier",
        "DEHUMIDIFIER": "dehumidifier",
        "INDUCTION_COOKER": "induction cooker",
        "AIR_PURIFIER": "air purifier",
        "WASHING_MACHINE": "washing machine",
        "WATER_HEATER": "water heater",
        "GAS_STOVE": "gas stove",
        "TV_SET": "tv",
        "OTT_BOX": "ott box",
        "RANGE_HOOD": "range hood",
        "FAN": "fan",
        "PROJECTOR": "projector",
        "SWEEPING_ROBOT": "robot vacuum",
        "KETTLE": "kettle",
        "MICROWAVE_OVEN": "microwave",
        "PRESSURE_COOKER": "pressure cooker",
        "RICE_COOKER": "rice cooker",
        "HIGH_SPEED_BLENDER": "blender",
        "AIR_FRESHER": "air fresher",
        "CLOTHES_RACK": "clothes rack",
        "OVEN": "oven",
        "STEAM_OVEN": "steam oven",
        "STEAM_BOX": "steamer",
        "HEATER": "heater",
        "WINDOW_OPENER": "window opener",
        "WEBCAM": "webcam",
        "CAMERA": "camera",
        "ROBOT": "robot",
        "PRINTER": "printer",
        "WATER_COOLER": "water cooler",
        "FISH_TANK": "fish tank",
        "WATERING_DEVICE": "watering device",
        "SET_TOP_BOX": "set top box",
        "AROMATHERAPY_MACHINE": "aromatherapy machine",
        "DVD": "dvd",
        "SHOE_CABINET": "shoe cabinet",
        "WALKING_MACHINE": "walking machine",
        "TREADMILL": "treadmill",
        "BED": "bed",
        "YUBA": "bath heater",
        "SHOWER": "shower",
        "BATHTUB": "bathtub",
        "DISINFECTION_CABINET": "disinfection cabinet",
        "DISHWASHER": "dishwasher",
        "SOFA": "sofa",
        "DOOR_BELL": "door bell",
        "ELEVATOR": "elevator",
        "WEIGHT_SCALE": "weight scale",
        "BODY_FAT_SCALE": "body fat scale",
        "WALL_HUNG_GAS_BOILER": "gas boiler",
        "SCENE_TRIGGER": "scene trigger",
        "ACTIVITY_TRIGGER": "activity trigger",
    }


    device_type_map_h2p = {
        'climate': 'AIR_CONDITION',
        'fan': 'FAN',
        'light': 'LIGHT',
        'media_player': 'TV_SET',
        'switch': 'SWITCH',
        'sensor': 'SENSOR',
        'cover': 'CURTAIN',
        'vacuum': 'SWEEPING_ROBOT',
        'humidifier': 'DEHUMIDIFIER',
        }

    _service_map_p2h = {
        # 妯″紡鍜屽钩鍙拌澶囩被鍨嬩笉褰卞搷
        'fan': {
            'IncrementFanSpeedRequest': lambda state, attributes, payload: (['fan'], ['increase_speed'], [{'percentage_step': 20}]),
            'DecrementFanSpeedRequest': lambda state, attributes, payload: (['fan'], ['decrease_speed'], [{'percentage_step': 20}]),
            'SetFanSpeedRequest': lambda state, attributes, payload: (['fan'], ['set_percentage'], [{'percentage': min(payload['fanSpeed']['value']*25,100)}]),
            'SetModeRequest': lambda state, attributes, payload: (['fan'], [payload['mode']['value'].lower().replace('swing','oscillate')], [{'oscillating': 'true'}]),
            'UnsetModeRequest': lambda state, attributes, payload: (['fan'], [payload['mode']['value'].lower().replace('swing','oscillate')], [{'oscillating': 'false'}]),
        },
        'climate': {
            'TurnOnRequest':  'turn_on',
            'TurnOffRequest': 'turn_off',
            'TimingTurnOnRequest': 'turn_on',
            'TimingTurnOffRequest': 'turn_off',
            'SetTemperatureRequest': lambda state, attributes, payload: (['climate'], ['set_temperature'], [{'temperature': payload['targetTemperature']['value']}]),
            'IncrementTemperatureRequest': lambda state, attributes, payload: (['climate'], ['set_temperature'],[ {'temperature': min(state.attributes['temperature'] + payload['deltaValue']['value'], 30)}]),
            'DecrementTemperatureRequest': lambda state, attributes, payload: (['climate'], ['set_temperature'], [{'temperature': max(state.attributes['temperature'] - payload['deltaValue']['value'], 16)}]),
            'SetModeRequest': lambda state, attributes, payload: (['climate'], ['set_hvac_mode'], [{'hvac_mode': payload['mode']['value'].lower().replace('fan','fan_only').replace('dehumidification','dry')}]),
            'SetFanSpeedRequest': lambda state, attributes, payload: (['climate'], ['set_fan_mode'], [{'fan_mode': payload['fanSpeed']['level'].replace('middle','medium').replace('_','-').replace('quite','Quiet').replace('min','Quiet').replace('powerful','Turbo')}]), 
        },
        'media_player': {
            'TurnOnRequest':  'turn_on',
            'TurnOffRequest': 'turn_off',
            'TimingTurnOnRequest': 'turn_on',
            'TimingTurnOffRequest': 'turn_off', 
            'PauseRequest': 'media_pause',
            'ContinueRequest': 'media_play',
            'IncrementTVChannelRequest': lambda state, attributes, payload: (['wukongtv'], ['tv_up']),
            'DecrementTVChannelRequest': lambda state, attributes, payload: (['wukongtv'], ['tv_down']),
            'IncrementVolumeRequest': 'volume_up',
            'DecrementVolumeRequest': 'volume_down',
            'SetVolumeRequest': lambda state, attributes, payload: (['media_player'], ['volume_set'], [{'volume_level': payload['deltaValue']['value']}]),
            'SetVolumeMuteRequest': 'volume_mute',
        },
        'humidifier': {
            'TurnOnRequest':  'turn_on',
            'TurnOffRequest': 'turn_off',
            'TimingTurnOnRequest': 'turn_on',
            'TimingTurnOffRequest': 'turn_off', 
            'SetHumidityRequest': lambda state, attributes, payload: (['humidifier'], ['set_humidity'], [{'temperature': payload['deltValue']['value']}]),
        },
        'cover': {
            'TurnOnRequest':  'open_cover',
            'TurnOffRequest': 'close_cover',
            'TimingTurnOnRequest': 'open_cover',
            'TimingTurnOffRequest': 'close_cover', 
            'PauseRequest': 'stop_cover',
        },
        'vacuum': {
            'TurnOnRequest':  'start',
            'TurnOffRequest': 'return_to_base',
            'TimingTurnOnRequest': 'start',
            'TimingTurnOffRequest': 'return_to_base',
            'SetSuctionRequest': lambda state, attributes, payload: (['vacuum'], ['set_fan_speed'], [{'fan_speed': 90 if payload['suction']['value'] == 'STRONG' else 60}]),
        },
        'switch': {
            'TurnOnRequest': 'turn_on',
            'TurnOffRequest': 'turn_off',
            'TimingTurnOnRequest': lambda state, attributes, payload: (['common_timer'], ['set'], [{'operation': 'on', 'duration': int(payload['timestamp']['value']) - int(time.time())}]),
            'TimingTurnOffRequest': lambda state, attributes, payload: (['common_timer'], ['set'], [{'operation': 'off', 'duration': int(payload['timestamp']['value']) - int(time.time())}])
        },
        'light': {
            'TurnOnRequest': 'turn_on',
            'TurnOffRequest': 'turn_off',
            'TimingTurnOnRequest': lambda state, attributes, payload: (['common_timer'], ['set'], [{'operation': 'on', 'duration': int(payload['timestamp']['value']) - int(time.time())}]),
            'TimingTurnOffRequest': lambda state, attributes, payload: (['common_timer'], ['set'], [{'operation': 'off', 'duration': int(payload['timestamp']['value']) - int(time.time())}]),
            'SetBrightnessPercentageRequest': lambda state, attributes, payload: (['light'], ['turn_on'], [{'brightness_pct': payload['brightness']['value']}]),
            'IncrementBrightnessPercentageRequest': lambda state, attributes, payload: (['light'], ['turn_on'],[ {'brightness_pct': min(state.attributes['brightness'] / 255 * 100 + payload['deltaPercentage']['value'], 100)}]),
            'DecrementBrightnessPercentageRequest': lambda state, attributes, payload: (['light'], ['turn_on'], [{'brightness_pct': max(state.attributes['brightness'] / 255 * 100 - payload['deltaPercentage']['value'], 0)}]),
            'SetColorRequest': lambda state, attributes, payload: (['light'], ['turn_on'], [{'hs_color': [float(payload['color']['hue']), float(payload['color']['saturation']) * 100], 'brightness_pct': float(payload['color']['brightness']) * 100}]),
            'SetColorTemperatureRequest': lambda state, attributes, payload: (['light'], ['turn_on'], [{'kelvin': payload['colorTemperatureInKelvin']}]),
            'IncrementColorTemperatureRequest': lambda state, attributes, payload: (['light'], ['turn_on'],[ {'kelvin': min(state.attributes['color_temp_kelvin'] + payload['deltaPercentage']['value'] * (int(state.attributes['max_color_temp_kelvin']) - int(state.attributes['min_color_temp_kelvin'])) / 100, state.attributes['max_color_temp_kelvin'])}]),
            'DecrementColorTemperatureRequest': lambda state, attributes, payload: (['light'], ['turn_on'], [{'kelvin': max(state.attributes['color_temp_kelvin'] - payload['deltaPercentage']['value'] * (int(state.attributes['max_color_temp_kelvin']) - int(state.attributes['min_color_temp_kelvin'])) / 100, state.attributes['min_color_temp_kelvin'])}]),
        },
        'havcs':{
            'TurnOnRequest': lambda state, attributes, payload:([cmnd[0] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['turn_on']], [cmnd[1] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['turn_on']], [json.loads(cmnd[2]) for cmnd in attributes[ATTR_DEVICE_ACTIONS]['turn_on']]) if attributes.get(ATTR_DEVICE_ACTIONS) else (['input_boolean'], ['turn_on'], [{}]),
            'TurnOffRequest': lambda state, attributes, payload:([cmnd[0] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['turn_off']], [cmnd[1] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['turn_off']], [json.loads(cmnd[2]) for cmnd in attributes[ATTR_DEVICE_ACTIONS]['turn_off']]) if attributes.get(ATTR_DEVICE_ACTIONS) else (['input_boolean'], ['turn_off'], [{}]),
            'IncrementBrightnessPercentageRequest': lambda state, attributes, payload:([cmnd[0] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['increase_brightness']], [cmnd[1] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['increase_brightness']], [json.loads(cmnd[2]) for cmnd in attributes[ATTR_DEVICE_ACTIONS]['increase_brightness']]) if attributes.get(ATTR_DEVICE_ACTIONS) else (['input_boolean'], ['turn_on'], [{}]),
            'DecrementBrightnessPercentageRequest': lambda state, attributes, payload:([cmnd[0] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['decrease_brightness']], [cmnd[1] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['decrease_brightness']], [json.loads(cmnd[2]) for cmnd in attributes[ATTR_DEVICE_ACTIONS]['decrease_brightness']]) if attributes.get(ATTR_DEVICE_ACTIONS) else (['input_boolean'], ['turn_on'], [{}]),                 
            'TimingTurnOnRequest': lambda state, attributes, payload: (['common_timer'], ['set'], [{'operation': 'custom:havcs_actions/timing_turn_on', 'duration': int(payload['timestamp']['value']) - int(time.time())}]),
            'TimingTurnOffRequest': lambda state, attributes, payload: (['common_timer'], ['set'], [{'operation': 'custom:havcs_actions/timing_turn_off', 'duration': int(payload['timestamp']['value']) - int(time.time())}]),
            'IncrementColorTemperatureRequest': lambda state, attributes, payload:([cmnd[0] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['increment_colortemperature']], [cmnd[1] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['increment_colortemperature']], [json.loads(cmnd[2]) for cmnd in attributes[ATTR_DEVICE_ACTIONS]['increment_colortemperature']]) if attributes.get(ATTR_DEVICE_ACTIONS) else (['input_boolean'], ['turn_on'], [{}]),
            'DecrementColorTemperatureRequest': lambda state, attributes, payload:([cmnd[0] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['decrease_colortemperature']], [cmnd[1] for cmnd in attributes[ATTR_DEVICE_ACTIONS]['decrease_colortemperature']], [json.loads(cmnd[2]) for cmnd in attributes[ATTR_DEVICE_ACTIONS]['decrease_colortemperature']]) if attributes.get(ATTR_DEVICE_ACTIONS) else (['input_boolean'], ['turn_on'], [{}]),                 
        }

    }
    # action:[{Platfrom Attr: HA Attr},{}]
    _query_map_p2h = {
        'GetTemperatureReadingRequest':{'temperatureReading':{'value':'%temperature','scale': 'CELSIUS'}},
    }


class VoiceControlDueros(PlatformParameter, VoiceControlProcessor):
    def __init__(self, hass, mode, entry):
        self._hass = hass
        self._mode = mode
        self.vcdm = VoiceControlDeviceManager(entry, DOMAIN, self.device_action_map_h2p, self.device_attribute_map_h2p, self._service_map_p2h, self.device_type_map_h2p, self._device_type_alias)
    def _errorResult(self, errorCode, messsage=None):
        """Generate error result"""
        error_code_map = {
            'INVALIDATE_CONTROL_ORDER': 'invalidate control order',
            'SERVICE_ERROR': 'TargetConnectivityUnstableError',
            'DEVICE_NOT_SUPPORT_FUNCTION': 'NotSupportedInCurrentModeError',
            'INVALIDATE_PARAMS': 'ValueOutOfRangeError',
            'DEVICE_IS_NOT_EXIST': 'DriverInternalError',
            'IOT_DEVICE_OFFLINE': 'TargetOfflineError',
            'ACCESS_TOKEN_INVALIDATE': 'InvalidAccessTokenError'            
        }
        messages = {
            'INVALIDATE_CONTROL_ORDER': 'invalidate control order',
            'SERVICE_ERROR': 'service error',
            'DEVICE_NOT_SUPPORT_FUNCTION': 'device not support',
            'INVALIDATE_PARAMS': 'invalidate params',
            'DEVICE_IS_NOT_EXIST': 'device is not exist',
            'IOT_DEVICE_OFFLINE': 'device is offline',
            'ACCESS_TOKEN_INVALIDATE': 'access_token is invalidate'
        }
        return {'errorCode': error_code_map.get(errorCode, 'undefined'), 'message': messsage if messsage else messages.get(errorCode, 'undefined')}

    def _to_number(self, value):
        if isinstance(value, (int, float)):
            return value
        if value is None:
            return None
        if isinstance(value, str):
            candidate = value.strip().replace('℃', '').replace('°C', '').replace('%', '')
            try:
                if '.' in candidate:
                    return float(candidate)
                return int(candidate)
            except ValueError:
                return value
        return value

    def _query_action_from_property(self, device_property):
        raw_attr = str(device_property.get('attribute', ''))
        mapped_attr = self.device_attribute_map_h2p.get(raw_attr, '')
        candidates = [
            f"query_{raw_attr}",
            f"query_{raw_attr.replace('_', '')}",
            f"query_{mapped_attr}",
            f"query_{str(mapped_attr).replace('_', '').lower()}",
        ]
        for candidate in candidates:
            action = self.device_action_map_h2p.get(candidate)
            if action:
                return action
        return None
    async def handleRequest(self, data, auth = False, request_from = "http"):
        """Handle request"""
        _LOGGER.info("[%s] Handle Request:\n%s", LOGGER_NAME, data)

        header = self._prase_command(data, 'header')
        action = self._prase_command(data, 'action')
        namespace = self._prase_command(data, 'namespace')
        p_user_id = self._prase_command(data, 'user_uid')
        result = {}
        # uid = p_user_id+'@'+DOMAIN

        if auth:
            namespace = header['namespace']
            if namespace == 'DuerOS.ConnectedHome.Discovery':
                action = 'DiscoverAppliancesResponse'
                err_result, discovery_devices, entity_ids = self.process_discovery_command(request_from)
                result = {'discoveredAppliances': discovery_devices}
                if DATA_HAVCS_BIND_MANAGER in self._hass.data[INTEGRATION]:
                    await self._hass.data[INTEGRATION][DATA_HAVCS_BIND_MANAGER].async_save_changed_devices(entity_ids, DOMAIN, p_user_id)
            elif namespace == 'DuerOS.ConnectedHome.Control':
                err_result, properties = await self.process_control_command(data)
                result = err_result if err_result else {'attributes': properties}
                action = action.replace('Request', 'Confirmation') # fix
            elif namespace == 'DuerOS.ConnectedHome.Query':
                err_result, properties = self.process_query_command(data)
                result = err_result if err_result else properties
                action = action.replace('Request', 'Response') # fix 涓诲姩涓婃姤浼氭敹鍒癛eportStateRequest action锛屽彲浠ヨ繑鍥炶澶囩殑鍏朵粬灞炴€т俊鎭笉瓒呰繃10涓?            else:
                result = self._errorResult('SERVICE_ERROR')
        else:
            result = self._errorResult('ACCESS_TOKEN_INVALIDATE')
        
        # Check error
        header['name'] = action
        if 'errorCode' in result:
            header['name'] = result['errorCode']
            result={}

        response = {'header': header, 'payload': result}

        _LOGGER.info("[%s] Respnose: %s", LOGGER_NAME, response)
        return response

    def _prase_command(self, command, arg):
        header = command['header']
        payload = command['payload']

        if arg == 'device_id':
            return payload['appliance']['applianceId']
        elif arg == 'action':
            return header['name']
        elif arg == 'user_uid':
            return payload.get('openUid','')
        else:
            return command.get(arg)

    def _discovery_process_propertites(self, device_properties):
        properties = []
        for device_property in device_properties:
            name = self.device_attribute_map_h2p.get(device_property.get('attribute'))
            state = self._hass.states.get(device_property.get('entity_id'))
            if name:
                value = state.state if state else 'unavailable'
                if name == 'temperatureReading':
                    value = self._to_number(value)
                    scale = 'CELSIUS'
                    legalValue = 'DOUBLE'
                elif name == 'targetTemperature':
                    value = self._to_number(value)
                    scale = 'CELSIUS'
                    legalValue = 'DOUBLE'
                elif name == 'brightness':
                    scale = '%'
                    legalValue = '[0.0, 100.0]'
                elif name == 'humidity':
                    value = self._to_number(value)
                    scale = '%'
                    legalValue = '[0.0, 100.0]'
                elif name == 'AQI':
                    value = self._to_number(value)
                    scale = ''
                    legalValue = 'INTEGER'
                elif name == 'PM25':
                    value = self._to_number(value)
                    scale = '渭g/m3'
                    legalValue = 'DOUBLE'
                elif name == 'PM10':
                    value = self._to_number(value)
                    scale = '渭g/m3'
                    legalValue = 'DOUBLE'
                elif name == 'ppm':
                    value = self._to_number(value)
                    scale = 'ppm'
                    legalValue = 'DOUBLE'
                elif name == 'hcho':
                    value = self._to_number(value)
                    scale = 'mg/m鲁'
                    legalValue = 'DOUBLE'
                elif name == 'turnOnState':
                    if value != 'on':
                        value = 'OFF'
                    else:
                        value = 'ON'
                    scale = ''
                    legalValue = '(ON, OFF)'
                elif name == 'havcmode':
                    scale = ''
                    legalValue = '("off", "heat_cool", "cool", "heat", "fan_only", "dry")'
                elif name == 'mode':
                    scale = ''
                    legalValue = '(POWERFUL, NORMAL, QUIET)'
                else:
                    _LOGGER.warning("[%s] %s has unsport attribute %s", LOGGER_NAME, device_property.get('entity_id'), name)
                    continue
                properties += [{'name': name, 'value': value, 'scale': scale, 'timestampOfSample': int(time.time()), 'uncertaintyInMilliseconds': 1000, 'legalValue': legalValue }]
        _LOGGER.debug(properties)
        _LOGGER.debug("properties list")
        return properties if properties else [{'name': 'turnOnState', 'value': 'OFF', 'scale': '', 'timestampOfSample': int(time.time()), 'uncertaintyInMilliseconds': 1000, 'legalValue': '(ON, OFF)' }]        
    def _discovery_process_actions(self, device_properties, raw_actions):
        actions = []
        for device_property in device_properties:
            action = self._query_action_from_property(device_property)
            if action:
                actions += [action,]
        for raw_action in raw_actions:
            action = self.device_action_map_h2p.get(raw_action)
            if action:
                actions += [action,]
        return list(set(actions))
    def _discovery_process_device_type(self, raw_device_type):
        # raw_device_type guess from device_id's domain transfer to platform style
        return raw_device_type if raw_device_type in self._device_type_alias else self.device_type_map_h2p.get(raw_device_type)

    def _discovery_process_device_info(self, device_id,  device_type, device_name, zone, properties, actions):
        return {
            'applianceId': encrypt_device_id(device_id),
            'friendlyName': device_name,
            'friendlyDescription': device_name,
            'additionalApplianceDetails': [],
            'applianceTypes': [device_type],
            'isReachable': True,
            'manufacturerName': 'HomeAssistant',
            'modelName': 'HomeAssistant',
            'version': '1.0',
            'actions': actions,
            'attributes': properties,
            }


    def _control_process_propertites(self, device_properties, action) -> None:
        
        return self._discovery_process_propertites(device_properties)

    def _query_process_propertites(self, device_properties, action) -> None:
        properties = {}
        queryresponseattributes = ["humidity", "turnonstate", "state", "location"]
        action = action.replace('Request', '').replace('Get', '')
        if action in self._query_map_p2h:
            for property_name, attr_template in self._query_map_p2h[action].items():
                formattd_property = self.vcdm.format_property(self._hass, device_properties, attr_template)
                if isinstance(formattd_property, dict) and 'value' in formattd_property:
                    formattd_property['value'] = self._to_number(formattd_property.get('value'))
                properties.update({property_name: formattd_property})
                _LOGGER.debug("properties=  %s : %s", property_name, formattd_property)
        else:
            for device_property in device_properties:
                _LOGGER.debug("device_property")
                _LOGGER.debug(device_property)
                state = self._hass.states.get(device_property.get('entity_id'))
                value = state.attributes.get(device_property.get('attribute'), state.state) if state else None
                _LOGGER.debug(state)
                _LOGGER.debug(value)
                if device_property.get('entity_id').startswith('climate.') and action == "TemperatureReading":
                    value = state.attributes.get("current_temperature", state.state) if state else None
                if device_property.get('entity_id').startswith('humidifier.') and action == "Humidity":
                    value = state.attributes.get("current_humidity", state.state) if state else None
                if device_property.get('entity_id').startswith('humidifier.') and action == "TargetHumidity":
                    value = state.attributes.get("humidity", state.state) if state else None
                if value is not None:
                    if device_property.get('attribute').lower() in action.lower():
                        name = action[0].lower() + action[1:]
                        name = name.replace("targetHumidity", "humidity")
                        name = name.replace("airPM25", "PM25")
                        name = name.replace("airPM10", "PM10")
                        name = name.replace("cO2Quantity", "ppm")
                        name = name.replace("airQualityIndex", "AQI")
                        if name in {"temperatureReading", "targetTemperature", "humidity", "PM25", "PM10", "ppm", "AQI", "hcho"}:
                            value = self._to_number(value)
                        _LOGGER.debug(name)
                        if name.lower() in queryresponseattributes:
                            if name == 'humidity':
                                scale = '%'
                            elif name == 'state':
                                scale = ''
                            elif name == 'location':
                                scale = ''
                            elif name == 'turnOnState':
                                if value != 'on':
                                    value = 'OFF'
                                else:
                                    value = 'ON'
                                scale = ''
                            formattd_property = {"attributes": [{'name': name, 'value': value, 'scale': scale, 'timestampOfSample': int(time.time()), 'uncertaintyInMilliseconds': 1000}]}
                        else:
                            formattd_property = {name: {'value': value}}
                        properties.update(formattd_property)
                    _LOGGER.debug("value锛?s", value)
        return properties
    def _decrypt_device_id(self, device_id) -> None:
        return decrypt_device_id(device_id)

    def report_device(self, device_id):

        payload = []
        for p_user_id in self._hass.data[INTEGRATION][DATA_HAVCS_BIND_MANAGER].get_uids(DOMAIN, device_id):
            _LOGGER.info("[%s] report device for %s:\n", LOGGER_NAME, p_user_id)
            report = {
                "header": {
                    "namespace": "DuerOS.ConnectedHome.Control",
                    "name": "ChangeReportRequest",
                    "messageId": str(uuid.uuid4()),
                    "payloadVersion": "1"
                },
                "payload": {
                    "botId": "",
                    "openUid": p_user_id,
                    "appliance": {
                        "applianceId": encrypt_device_id(device_id),
                        "attributeName": "turnOnState"
                    }
                }
            }
            payload.append(report)
        return payload

