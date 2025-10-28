import pandas as pd

import os, sys

from .utils import PATH_TO_ROOT
if str(PATH_TO_ROOT) not in sys.path:
    sys.path.append(str(PATH_TO_ROOT))
from src.modules.services.service_basis.user_info import UserInfo
from src.modules.services.service_basis.basis.tool import Tool

# 路径常量集中管理

TICKET_CSV_PATH = PATH_TO_ROOT / 'dataset' / 'ticket_service' / 'ticket.csv'


ticketquery_desc = '''车票查询：本接口用于从数据库中查询符合用户要求的火车票。接口输入格式：{"起始站":<起始高铁站>, "终点站":<终点高铁站>, "发车日期":<发车日期>, "到站日期":<到站日期>, "最早发车时刻":<最早发车时刻>, "最晚发车时刻":<最晚发车时刻>, "最早到站时刻":<最早到站时刻>, "最晚到站时刻":<最晚到站时刻>}，其中：时刻的格式都应该形如"08:15"、日期的格式都应该形如"2025-6-7"、起始站和终点站不可缺失、用None作缺失值表示不作要求'''

class TicketQuery(Tool):
    """
    票务查询模块，负责查询票务信息
    """
    def __init__(self, name="车票查询", description=ticketquery_desc):
        super().__init__(name, description)
        # 兼容容器和本地开发环境，始终从项目根目录定位 dataset/ticket.csv
        self.tickets = pd.read_csv(TICKET_CSV_PATH, low_memory=False)
        self.tickets.drop('软卧/动卧/一等卧', axis=1, inplace=True)
        self.tickets = self.tickets.groupby(['起始站', '终点站']).apply(lambda X: X)
        self.tickets['出发日期'] = pd.to_datetime(self.tickets['出发日期'], format="mixed")
        self.tickets['到达日期'] = pd.to_datetime(self.tickets['到达日期'], format='mixed')
        self.tickets['出发时间'] = pd.to_datetime(self.tickets['出发时间'], format='mixed')
        self.tickets['到达时间'] = pd.to_datetime(self.tickets['到达时间'], format='mixed')
        
        # 创建城市名到车站名的映射
        self._build_city_station_mapping()
    
    def _build_city_station_mapping(self):
        """构建城市名到车站名的映射关系"""
        all_stations = set(self.tickets.index.get_level_values('起始站').unique()) | \
                      set(self.tickets.index.get_level_values('终点站').unique())
        
        self.city_to_stations = {}
        
        # 主要城市的映射规则
        city_patterns = {
            '北京': ['北京', '北京南', '北京西', '北京丰台', '北京大兴', '北京朝阳', '北京北'],
            '上海': ['上海', '上海虹桥', '上海南', '上海松江', '上海西'],
            '广州': ['广州', '广州南', '广州东', '广州北', '广州白云'],
            '深圳': ['深圳', '深圳北', '深圳东'],
            '天津': ['天津', '天津南', '天津西'],
            '杭州': ['杭州', '杭州东', '杭州南'],
            '南京': ['南京', '南京南', '南京西'],
            '武汉': ['武汉', '武汉站'],
            '成都': ['成都', '成都东', '成都南'],
            '重庆': ['重庆', '重庆北', '重庆西'],
            '西安': ['西安', '西安北'],
            '郑州': ['郑州', '郑州东'],
            '长沙': ['长沙', '长沙南'],
            '沈阳': ['沈阳', '沈阳北', '沈阳南'],
            '大连': ['大连', '大连北'],
            '青岛': ['青岛', '青岛北'],
            '济南': ['济南', '济南东', '济南西'],
            '哈尔滨': ['哈尔滨', '哈尔滨西'],
            '长春': ['长春', '长春西'],
            '石家庄': ['石家庄'],
            '太原': ['太原', '太原南'],
            '合肥': ['合肥', '合肥南'],
            '福州': ['福州', '福州南'],
            '厦门': ['厦门', '厦门北'],
            '南昌': ['南昌', '南昌西'],
            '昆明': ['昆明', '昆明南'],
            '贵阳': ['贵阳', '贵阳北'],
            '兰州': ['兰州', '兰州西'],
            '银川': ['银川'],
            '西宁': ['西宁'],
            '乌鲁木齐': ['乌鲁木齐', '乌鲁木齐南']
        }
        
        # 构建映射关系
        for city, potential_stations in city_patterns.items():
            actual_stations = [station for station in potential_stations if station in all_stations]
            if actual_stations:
                self.city_to_stations[city] = actual_stations
        
        # 添加直接匹配（车站名本身）
        for station in all_stations:
            if station not in self.city_to_stations:
                self.city_to_stations[station] = [station]
    
    def _find_matching_stations(self, city_input):
        """根据输入的城市名或车站名找到匹配的车站列表"""
        # 直接匹配
        if city_input in self.city_to_stations:
            return self.city_to_stations[city_input]
        
        # 模糊匹配：查看是否有车站名包含输入的城市名
        matching_stations = []
        all_stations = set(self.tickets.index.get_level_values('起始站').unique()) | \
                      set(self.tickets.index.get_level_values('终点站').unique())
        
        for station in all_stations:
            if city_input in station:
                matching_stations.append(station)
        
        return matching_stations if matching_stations else None

    # 反馈查询失败的原因与相关的数据库细节
    def __call__(self, parameter: dict, user_info: UserInfo, history: list) -> list:
        """
        查询票务信息
        :param user_info: 用户信息
        :return: 查询的票务信息
        [
'找到5条路线：重庆北 → 上海, 重庆北 → 上海松江, 重庆北 → 上海南, 重庆北 → 上海虹桥, 重庆西 → 上海虹桥', 
	{
		'出发日期': Timestamp('2025-05-11 00:00:00'), 
		'车次': 'Z258', 
		'起始站': '重庆北',
		'终点站': '上海南',
		'出发时间': Timestamp('2025-10-26 14:10:00'), 
		'到达时间': Timestamp('2025-10-26 08:18:00'), 
		'历时': '18:08', 
		'硬卧/二等卧': '无', 
		'到达日期': Timestamp('2025-05-12 00:00:00')
	}, 
	{
		'出发日期': Timestamp('2025-05-11 00:00:00'), 
		'车次': 'Z258', 
		'起始站': '重庆北', 
		'终点站': '上海松江', 
		'出发时间': Timestamp('2025-10-26 14:10:00'), 
		'到达时间': Timestamp('2025-10-26 07:32:00'), 
		'历时': '17:22', 
		'硬卧/二等卧': '无', 
		'到达日期': Timestamp('2025-05-12 00:00:00')
	}
]
        """

        l_info = []
        
        # 安全获取参数，添加缺失值检查
        try:
            src = parameter['起始站']
            des = parameter['终点站']
        except KeyError as e:
            return [f'缺少必需参数: {str(e)}']
        
        # 查找匹配的车站
        src_stations = self._find_matching_stations(src)
        des_stations = self._find_matching_stations(des)
        
        if not src_stations:
            all_src_stations = list(set(self.tickets.index.get_level_values('起始站').unique()))[:10]
            return [f'找不到起始站"{src}"，可用的起始站示例：{all_src_stations}']
        
        if not des_stations:
            all_des_stations = list(set(self.tickets.index.get_level_values('终点站').unique()))[:10]
            return [f'找不到终点站"{des}"，可用的终点站示例：{all_des_stations}']
        
        # 安全转换时间参数，处理None值
        def safe_timestamp(value):
            if value is None or pd.isna(value):
                return pd.NaT
            try:
                return pd.Timestamp(value)
            except:
                return pd.NaT
                
        s_date = safe_timestamp(parameter.get('发车日期'))
        e_date = safe_timestamp(parameter.get('到站日期'))
        l_dept_time = safe_timestamp(parameter.get('最早发车时刻'))
        r_dept_time = safe_timestamp(parameter.get('最晚发车时刻'))
        l_arrv_time = safe_timestamp(parameter.get('最早到站时刻'))
        r_arrv_time = safe_timestamp(parameter.get('最晚到站时刻'))
        
        # 收集所有匹配的路线
        all_results = []
        route_info = []
        
        for src_station in src_stations:
            for des_station in des_stations:
                try:
                    # 尝试查找从src_station到des_station的路线
                    route_results = self.tickets.loc[src_station].loc[des_station]
                    if not route_results.empty:
                        all_results.append(route_results)
                        route_info.append(f"{src_station} → {des_station}")
                except KeyError:
                    continue
        
        if not all_results:
            return [f'找不到从"{src}"到"{des}"的直达车次。匹配的起始站：{src_stations}，匹配的终点站：{des_stations}']
        
        # 合并所有结果
        results = pd.concat(all_results, ignore_index=False)
        
        # 应用时间和日期过滤条件
        if not pd.isna(s_date) and (results['出发日期'] == s_date).sum() == 0:
            # 获取可用的出发日期
            available_dates = sorted(results['出发日期'].dt.strftime('%Y-%m-%d').unique())
            l_info.append(f'出发日期为{s_date.strftime("%Y-%m-%d")}的车次不存在，可用的出发日期有：{", ".join(available_dates[:5])}')
            # 如果指定日期不存在，显示所有可用车次而不是返回空结果
        elif not pd.isna(s_date):
            results = results[results['出发日期'] == s_date]
            
        if not pd.isna(e_date) and (results['到达日期'] == e_date).sum() == 0:
            available_dates = sorted(results['到达日期'].dt.strftime('%Y-%m-%d').unique())
            l_info.append(f'到站日期为{e_date.strftime("%Y-%m-%d")}的车次不存在，可用的到站日期有：{", ".join(available_dates[:5])}')
        elif not pd.isna(e_date):
            results = results[results['到达日期'] == e_date]
            
        if not pd.isna(l_dept_time) and (results['出发时间'] >= l_dept_time).sum() == 0:
            l_info.append(f'出发时间在{l_dept_time.strftime("%H:%M:%S")}之后的车次不存在')
        elif not pd.isna(l_dept_time):
            results = results[results['出发时间'] >= l_dept_time]
            
        if not pd.isna(r_dept_time) and (results['出发时间'] <= r_dept_time).sum() == 0:
            l_info.append(f'出发时间在{r_dept_time.strftime("%H:%M:%S")}之前的车次不存在')
        elif not pd.isna(r_dept_time):
            results = results[results['出发时间'] <= r_dept_time]
            
        if not pd.isna(l_arrv_time) and (results['到达时间'] >= l_arrv_time).sum() == 0:
            l_info.append(f'到站时间在{l_arrv_time.strftime("%H:%M:%S")}之后的车次不存在')
        elif not pd.isna(l_arrv_time):
            results = results[results['到达时间'] >= l_arrv_time]
            
        if not pd.isna(r_arrv_time) and (results['到达时间'] <= r_arrv_time).sum() == 0:
            l_info.append(f'到站时间在{r_arrv_time.strftime("%H:%M:%S")}之前的车次不存在')
        elif not pd.isna(r_arrv_time):
            results = results[results['到达时间'] <= r_arrv_time]

        # 处理查询结果
        try:
            # 添加路线信息说明
            if len(route_info) > 1:
                l_info.append(f'找到{len(route_info)}条路线：{", ".join(set(route_info))}')
            
            for _, result in results.iterrows():
                info = {}
                for idx in result.index.to_list():
                    if str(result[idx]) != 'nan':
                        info[idx] = result[idx]
                l_info.append(info)
            if len(l_info) > 6:  # 增加显示条数以包含提示信息
                l_info = l_info[:6]
        except Exception as e:
            l_info.append(f'处理查询结果时出错: {str(e)}')

        return l_info

class TicketQueryMappingDate(TicketQuery):
    """
    票务查询模块，负责查询票务信息
    """
    def __init__(self, name="车票查询", description=ticketquery_desc):
        super().__init__(name, description)

        self.departure_date_range: list[pd.Timestamp] = [self.tickets['出发日期'].min(), self.tickets['出发日期'].max()]
        self.arrive_date_range: list[pd.Timestamp] = [self.tickets['到达日期'].min(), self.tickets['到达日期'].max()]


    def mapping_date(self, date_str_0: str, date_str_1: str, valid_range: list[pd.Timestamp]) -> tuple[pd.Timestamp, pd.Timestamp]:
        """
        将用户输入的日期字符串映射到系统中的日期范围的中间，以提高匹配成功率；保存原有的日期格式和时间上的距离
        :param departure_date_str: 用户输入的出发日期字符串
        :param arrive_date_str: 用户输入的到达日期字符串
        :return: 映射后的日期范围描述
        """
        mid_tag = valid_range[0] + (valid_range[1] - valid_range[0]) / 2
        mapped_date_str_0 = pd.to_datetime(date_str_0, errors='coerce')
        mapped_date_str_1 = pd.to_datetime(date_str_1, errors='coerce')
        if pd.isna(mapped_date_str_0) or pd.isna(mapped_date_str_1):
            raise ValueError("需要有效的日期字符串进行映射")   
     
        # 将用户输入的区间平移到有效范围的中点附近，保留两端的间距
        mapped_date_str_1 = mid_tag + (mapped_date_str_1 - mapped_date_str_0)
        mapped_date_str_0 = mid_tag
        # 返回 pd.Timestamp 对象，调用方在需要时可以格式化为字符串或用于时间计算
        return mapped_date_str_0, mapped_date_str_1
    
    def __call__(self, parameter: dict, user_info: UserInfo, history: list) -> list:
        """
        查询票务信息
        :param user_info: 用户信息
        :return: 查询的票务信息
        """
        # 处理日期映射
        
        if parameter.get('发车日期') is None:
            parameter['发车日期'] = parameter.get('到站日期')
        if parameter.get('到站日期') is None:
            parameter['到站日期'] = parameter.get('发车日期')

        original_departure_date = parameter['发车日期']
        original_arrive_date = parameter['到站日期']
        parameter['发车日期'], parameter['到站日期'] = self.mapping_date(
            parameter['发车日期'],
            parameter['到站日期'],
            self.departure_date_range
        )
        """
        调用父类的查询方法
        [
'找到5条路线：重庆北 → 上海, 重庆北 → 上海松江, 重庆北 → 上海南, 重庆北 → 上海虹桥, 重庆西 → 上海虹桥', 
	{
		'出发日期': Timestamp('2025-05-11 00:00:00'), 
		'车次': 'Z258', 
		'起始站': '重庆北',
		'终点站': '上海南',
		'出发时间': Timestamp('2025-10-26 14:10:00'), 
		'到达时间': Timestamp('2025-10-26 08:18:00'), 
		'历时': '18:08', 
		'硬卧/二等卧': '无', 
		'到达日期': Timestamp('2025-05-12 00:00:00')
	}, 
	{
		'出发日期': Timestamp('2025-05-11 00:00:00'), 
		'车次': 'Z258', 
		'起始站': '重庆北', 
		'终点站': '上海松江', 
		'出发时间': Timestamp('2025-10-26 14:10:00'), 
		'到达时间': Timestamp('2025-10-26 07:32:00'), 
		'历时': '17:22', 
		'硬卧/二等卧': '无', 
		'到达日期': Timestamp('2025-05-12 00:00:00')
	}
]
        """
        ans = super().__call__(parameter, user_info, history)

        # remapped ans
        remapped_ans = []
        for item in ans:
            if isinstance(item, dict):
                item = item.copy()
                if '出发日期' in item:
                    delta_days = (item['出发日期'] - parameter['发车日期']).days
                    item['出发日期'] = pd.to_datetime(original_departure_date) + pd.Timedelta(days=delta_days)
                if '到达日期' in item:
                    delta_days = (item['到达日期'] - parameter['到站日期']).days
                    item['到达日期'] = pd.to_datetime(original_arrive_date) + pd.Timedelta(days=delta_days)
            remapped_ans.append(item)
        # 返回重映射后的结果列表
        return remapped_ans
if __name__ == '__main__':
    user_id = "130632196606166516"
    ticket_info = {"train_number": "G1001", "departure_time": "2024-12-20 09:00", "seat_type": "二等座"}
    user_info = UserInfo(user_id, ticket_info)

    ticket_query = TicketQuery()
    print(ticket_query({'起始站':'上', '终点站':'乌鲁木齐'}, user_info, history=[]))