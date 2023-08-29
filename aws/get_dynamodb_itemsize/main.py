import boto3


def calculate_item_size(item):
    # 参考：https://jsapachehtml.hatenablog.com/entry/2016/04/09/091248
    total_size = 0

    for key, value in item.items():
        # 属性名のバイト数を追加
        total_size += len(key.encode("utf-8"))

        # 属性値のデータ型に基づいてバイト数を計算
        if isinstance(value, (str, bytes)):
            total_size += len(str(value).encode("utf-8"))
        elif isinstance(value, (int, float)):
            total_size += len(str(value))
        elif isinstance(value, bool) or value is None:
            total_size += 1
        else:
            # その他のデータ型の場合、文字列としてのバイト数を追加
            total_size += len(str(value).encode("utf-8"))

    return total_size


def main(table_name):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # アイテムをフルスキャン
    items = []
    response = table.scan()
    items.extend(response["Items"])

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response["Items"])

    # アイテムのサイズを計算
    sizes = [(item, calculate_item_size(item)) for item in items]

    # 最大値、最小値、平均値を計算
    max_item = max(sizes, key=lambda x: x[1])
    min_item = min(sizes, key=lambda x: x[1])
    avg_size = sum(size for _, size in sizes) / len(sizes)

    # 中央値を計算
    sorted_sizes = sorted(sizes, key=lambda x: x[1])
    middle = len(sorted_sizes) // 2
    if len(sorted_sizes) % 2 == 0:
        median_size = (sorted_sizes[middle - 1][1] + sorted_sizes[middle][1]) / 2
        median_item = sorted_sizes[middle - 1][0]  # 偶数の場合、中央の前のアイテムを選択
    else:
        median_size = sorted_sizes[middle][1]
        median_item = sorted_sizes[middle][0]

    primary_key_name = [
        schema["AttributeName"]
        for schema in table.key_schema
        if schema["KeyType"] == "HASH"
    ][
        0
    ]  # プライマリキーの名前を取得
    print(f"最大サイズ: {max_item[1]} bytes, プライマリキー: {max_item[0][primary_key_name]}")
    print(f"最小サイズ: {min_item[1]} bytes, プライマリキー: {min_item[0][primary_key_name]}")
    print(f"中央値: {median_size} bytes, プライマリキー: {median_item[primary_key_name]}")
    print(f"平均サイズ: {avg_size:.2f} bytes")


if __name__ == "__main__":
    table_name_input = input("テーブル名を入力してください: ")
    main(table_name_input)
