# runtime gallery

- 이 디렉터리는 얼굴 갤러리 로컬 자산 전용이다.
- 새 기준에서는 사람별 폴더를 `person_id`로 만들고, 그 안에 `meta.json`과 `images/`를 둔다.
- 예시:
  - `gildong-1a2b3c4d/meta.json`
  - `gildong-1a2b3c4d/images/capture-1234abcd.jpg`
- `meta.json`에는 최소 `person_id`, `name_ko`, `name_en`, `created_at`, `updated_at`를 둔다.
- 예전 `한글이름, EnglishName` 폴더도 읽기는 지원하지만, 새 web API는 새 구조를 기준으로 다룬다.
- 한 장의 이미지에는 얼굴이 1개만 있는 구성이 가장 안전하다.
- 이 디렉터리 안의 실제 사용자 이미지는 git으로 추적하지 않는다.
