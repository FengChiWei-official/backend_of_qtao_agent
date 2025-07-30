import json
import pymysql
import ast

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': 'qwq233383',
    'database': 'tstDB'
}


def unescape_unicode(value):
    """将Unicode转义序列转换为实际字符"""
    try:
        # 处理JSON字符串中的Unicode转义
        return ast.literal_eval(f'"{value}"')
    except:
        return value


# 分批处理数据库记录
def process_json_column(batch_size=100):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    offset = 0

    while True:
        # 读取批量数据
        query = f"SELECT id, system_thoughts FROM dialogue_records WHERE system_thoughts LIKE '%\\u%' LIMIT {offset}, {batch_size}"
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            break

        for row in rows:
            try:
                # 处理JSON数据
                data = json.loads(row['system_thoughts'])

                # 递归遍历所有值
                def process_item(item):
                    if isinstance(item, dict):
                        return {k: process_item(v) for k, v in item.items()}
                    elif isinstance(item, list):
                        return [process_item(v) for v in item]
                    elif isinstance(item, str):
                        return unescape_unicode(item)
                    return item

                updated_data = process_item(data)
                updated_json = json.dumps(updated_data, ensure_ascii=False)

                # 更新数据库
                update_query = "UPDATE dialogue_records SET system_thoughts = %s WHERE id = %s"
                cursor.execute(update_query, (updated_json, row['id']))

            except json.JSONDecodeError:
                print(f"无效JSON数据 (ID {row['id']}), 跳过")

        offset += batch_size
        conn.commit()
        print(f"已处理 {offset} 条记录")

    conn.close()


# 执行处理
process_json_column()