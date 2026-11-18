"""package 명령 하나를 실행하면서,
호출된 package 함수를 호출 순서와 깊이대로 출력한다.

사용: uv run python scripts/trace_calls.py --session walk start demo
출력: 함수 이름과 파일:줄 (표준 오류). 명령 결과 JSON 은 원래대로 표준 출력.
"""

import sys

from package.entry.cli import main  # import 는 추적하지 않는다 (클래스 정의가 섞이지 않게)

SKIP = {"__post_init__", "to_dict", "from_dict", "<genexpr>", "<listcomp>", "<dictcomp>", "<lambda>"}
depth = 0


def tracer(frame, event, arg):  # type: ignore[no-untyped-def]
    global depth
    path = frame.f_code.co_filename
    if "/src/package/" not in path:
        return
    name = frame.f_code.co_qualname
    if event == "call":
        if name.split(".")[-1] not in SKIP:
            print(f"{'  ' * depth}{name}  {path.split('/src/')[1]}:{frame.f_lineno}", file=sys.stderr)
        depth += 1
    elif event == "return":
        depth -= 1


sys.setprofile(tracer)
code = main(sys.argv[1:])
sys.setprofile(None)
sys.exit(code)
