import json
from pathlib import Path

GAMES_FILE = Path("games.json")
BATCH_FILE = Path("new_batch.json")


def load_json_list(path: Path) -> list:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"{path.name}의 최상위 구조가 배열([ ... ])이 아닙니다.")
    return data


def main():
    existing_games = load_json_list(GAMES_FILE)
    new_games = load_json_list(BATCH_FILE)

    merged_by_id = {}
    errors = []
    warnings = []

    # 기존 목록 먼저 등록 (나중에 들어오는 새 목록이 같은 id면 덮어쓰기)
    for idx, item in enumerate(existing_games + new_games):
        if not isinstance(item, dict):
            errors.append(f"[{idx}] 항목이 객체({{...}}) 형태가 아닙니다.")
            continue

        app_id = item.get("id")
        title = item.get("title", "제목 없음")

        if not isinstance(app_id, int) or app_id <= 0:
            errors.append(f"[{idx}] '{title}'의 id가 올바른 양의 정수가 아닙니다: {app_id}")
            continue

        orig = item.get("orig", 0)
        current = item.get("current", 0)
        lowest = item.get("lowest", 0)
        avg = item.get("avg", 0)

        # 숫자 타입 검사
        if not all(isinstance(v, (int, float)) and v >= 0 for v in [orig, current, lowest, avg]):
            errors.append(f"AppID {app_id} ({title}): 가격 필드에 음수나 잘못된 값이 있습니다.")
            continue

        # 가격 논리 검사
        if orig > 0 and current > orig:
            warnings.append(f"AppID {app_id} ({title}): 현재가({current})가 정가({orig})보다 큽니다.")
        if lowest > 0 and current > 0 and lowest > current:
            warnings.append(f"AppID {app_id} ({title}): 역대최저가({lowest})가 현재가({current})보다 큽니다.")
        if orig == 0 and (current > 0 or lowest > 0):
            warnings.append(f"AppID {app_id} ({title}): 무료(orig=0)인데 가격이 0보다 큽니다.")

        # 할인율 자동 재계산
        if orig > 0 and current < orig:
            item["discount"] = round((1 - current / orig) * 100)
        else:
            item["discount"] = 0

        merged_by_id[app_id] = item

    # id 오름차순 정렬 후 저장
    final_list = sorted(merged_by_id.values(), key=lambda g: g["id"])
    GAMES_FILE.write_text(
        json.dumps(final_list, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"저장 완료: games.json에 총 {len(final_list)}개 게임이 반영되었습니다.")

    if warnings:
        print("\n[가격/데이터 점검 알림]")
        for w in warnings:
            print(" -", w)

    if errors:
        print("\n[형식 오류 목록]")
        for e in errors:
            print(" -", e)


if __name__ == "__main__":
    main()