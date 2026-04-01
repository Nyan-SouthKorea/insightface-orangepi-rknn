# calibration local results

- 이 디렉터리는 `INT8 calibration` 입력 이미지 묶음을 로컬 전용으로 두는 자리다.
- 실제 얼굴 이미지와 live snapshot은 private local 자산으로 보고 git에 넣지 않는다.
- canonical tracked 산출물은 여기의 이미지 묶음이 아니라 `conversion/results/model_zoo/` 아래 최종 `RKNN` pack이다.
- 새 calibration bundle은 `conversion/prepare_rknn_calibration_dataset.py`로 만들고, 생성 경로와 사용 pack은 `conversion/README.md`, `docs/logbook.md`에 기록한다.
