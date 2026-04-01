import { useEffect, useMemo, useState } from "react";

const emptyStatus = {
  available_model_packs: [],
  latest_results: [],
  latest_results_count: 0,
  frame_width: 0,
  frame_height: 0,
  model_pack: "buffalo_m",
};

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return response.json();
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function buildBoxStyle(result, status) {
  if (!status.frame_width || !status.frame_height) {
    return {};
  }
  const [x1, y1, x2, y2] = result.bbox;
  return {
    left: `${(x1 / status.frame_width) * 100}%`,
    top: `${(y1 / status.frame_height) * 100}%`,
    width: `${((x2 - x1) / status.frame_width) * 100}%`,
    height: `${((y2 - y1) / status.frame_height) * 100}%`,
  };
}

function overlayTitle(result) {
  if (result.kr_name && result.kr_name !== "Unknown") {
    return result.kr_name;
  }
  return result.en_name || "Unknown";
}

export default function App() {
  const [status, setStatus] = useState(emptyStatus);
  const [people, setPeople] = useState([]);
  const [selectedPersonId, setSelectedPersonId] = useState("");
  const [selectedModelPack, setSelectedModelPack] = useState("buffalo_m");
  const [newPersonForm, setNewPersonForm] = useState({ name_ko: "", name_en: "" });
  const [editForm, setEditForm] = useState({ name_ko: "", name_en: "" });
  const [busyLabel, setBusyLabel] = useState("");
  const [error, setError] = useState("");
  const [liveState, setLiveState] = useState("connecting");

  const selectedPerson = useMemo(
    () => people.find((person) => person.person_id === selectedPersonId) || null,
    [people, selectedPersonId],
  );

  const activePack = useMemo(
    () => status.available_model_packs.find((item) => item.model_pack === selectedModelPack),
    [selectedModelPack, status.available_model_packs],
  );

  const statusMessage = error || status.last_error || status.last_switch_error || "";

  async function refreshStatus() {
    const payload = await fetchJson("/api/status");
    setStatus((current) => ({
      ...current,
      ...payload,
      available_model_packs: payload.available_model_packs || current.available_model_packs || [],
    }));
    setSelectedModelPack((current) => current || payload.model_pack || "buffalo_m");
    return payload;
  }

  async function refreshPeople(preferredPersonId = null) {
    const payload = await fetchJson("/api/gallery/people");
    const items = payload.items || [];
    setPeople(items);

    const firstPersonId = items[0]?.person_id || "";
    const requestedPersonId = preferredPersonId || selectedPersonId || firstPersonId;
    const target =
      items.find((person) => person.person_id === requestedPersonId) || items[0] || null;

    setSelectedPersonId(target?.person_id || "");
    setEditForm({
      name_ko: target?.name_ko || "",
      name_en: target?.name_en || "",
    });
    return payload;
  }

  useEffect(() => {
    let isClosed = false;
    const peopleTimer = window.setInterval(() => {
      refreshPeople().catch((err) => {
        if (!isClosed) {
          setError(err.message);
        }
      });
    }, 15000);

    refreshStatus().catch((err) => {
      if (!isClosed) {
        setError(err.message);
      }
    });
    refreshPeople().catch((err) => {
      if (!isClosed) {
        setError(err.message);
      }
    });

    const eventSource = new EventSource("/api/live-state/stream");
    eventSource.addEventListener("state", (event) => {
      if (isClosed) {
        return;
      }
      try {
        const payload = JSON.parse(event.data);
        setLiveState("live");
        setStatus((current) => ({
          ...current,
          ...payload,
          available_model_packs: current.available_model_packs,
        }));
      } catch (err) {
        setError(err.message);
      }
    });
    eventSource.onopen = () => {
      if (!isClosed) {
        setLiveState("live");
      }
    };
    eventSource.onerror = () => {
      if (!isClosed) {
        setLiveState("reconnecting");
      }
    };

    return () => {
      isClosed = true;
      window.clearInterval(peopleTimer);
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    if (!selectedPerson) {
      return;
    }
    setEditForm({
      name_ko: selectedPerson.name_ko,
      name_en: selectedPerson.name_en,
    });
  }, [selectedPerson]);

  async function withBusy(label, action, options = {}) {
    const { preferredPersonId = null, refreshPeopleAfter = true } = options;
    setBusyLabel(label);
    setError("");
    try {
      const result = await action();
      await refreshStatus();
      if (refreshPeopleAfter) {
        await refreshPeople(preferredPersonId);
      }
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setBusyLabel("");
    }
  }

  async function handleSwitchModel() {
    await withBusy("모델 전환 중", async () => {
      await fetchJson("/api/model-pack/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_pack: selectedModelPack }),
      });
    });
  }

  async function handleCreatePerson(event) {
    event.preventDefault();
    try {
      const payload = await withBusy(
        "프로필 추가 중",
        async () =>
          fetchJson("/api/gallery/people", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newPersonForm),
          }),
        { refreshPeopleAfter: false },
      );
      setNewPersonForm({ name_ko: "", name_en: "" });
      await refreshPeople(payload.item.person_id);
    } catch {
      // handled in withBusy
    }
  }

  async function handleRenamePerson() {
    if (!selectedPerson) {
      return;
    }
    try {
      await withBusy(
        "이름 변경 저장 중",
        async () =>
          fetchJson(`/api/gallery/people/${selectedPerson.person_id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(editForm),
          }),
        { preferredPersonId: selectedPerson.person_id },
      );
    } catch {
      // handled in withBusy
    }
  }

  async function handleDeletePerson() {
    if (!selectedPerson) {
      return;
    }
    if (!window.confirm(`${selectedPerson.name_ko} 인물과 등록 이미지를 모두 삭제할까요?`)) {
      return;
    }
    try {
      await withBusy(
        "인물 삭제 중",
        async () =>
          fetchJson(`/api/gallery/people/${selectedPerson.person_id}`, {
            method: "DELETE",
          }),
        { refreshPeopleAfter: false },
      );
      await refreshPeople();
    } catch {
      // handled in withBusy
    }
  }

  async function handleCaptureImage() {
    if (!selectedPerson) {
      return;
    }
    try {
      await withBusy(
        "현재 프레임 등록 중",
        async () =>
          fetchJson(`/api/gallery/people/${selectedPerson.person_id}/images/capture`, {
            method: "POST",
          }),
        { preferredPersonId: selectedPerson.person_id },
      );
    } catch {
      // handled in withBusy
    }
  }

  async function handleUploadImages(event) {
    if (!selectedPerson) {
      return;
    }
    const files = Array.from(event.target.files || []);
    if (files.length === 0) {
      return;
    }

    try {
      await withBusy(
        "이미지 업로드 중",
        async () => {
          const formData = new FormData();
          files.forEach((file) => formData.append("files", file));
          const response = await fetch(`/api/gallery/people/${selectedPerson.person_id}/images/upload`, {
            method: "POST",
            body: formData,
          });
          if (!response.ok) {
            const payload = await response.json();
            throw new Error(payload.detail || "이미지 업로드에 실패했습니다.");
          }
          event.target.value = "";
        },
        { preferredPersonId: selectedPerson.person_id },
      );
    } catch {
      // handled in withBusy
    }
  }

  async function handleDeleteImage(imageId) {
    if (!selectedPerson) {
      return;
    }
    try {
      await withBusy(
        "이미지 삭제 중",
        async () =>
          fetchJson(`/api/gallery/people/${selectedPerson.person_id}/images/${imageId}`, {
            method: "DELETE",
          }),
        { preferredPersonId: selectedPerson.person_id },
      );
    } catch {
      // handled in withBusy
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <div className="eyebrow">InsightFace RKNN Console</div>
          <h1>OrangePI Face Runtime</h1>
          <p>
            SDK 상태, 실시간 얼굴 인식, 갤러리 관리, 모델 전환을 한 화면에서 운영할 수 있게 정리했습니다.
          </p>
        </div>
        <div className="hero-badges">
          <div className="hero-card">
            <span>현재 모델</span>
            <strong>{status.model_pack || "-"}</strong>
            <small>resolved: {status.resolved_model_pack || "-"}</small>
          </div>
          <div className="hero-card">
            <span>상태 연결</span>
            <strong>{liveState === "live" ? "LIVE" : "RETRY"}</strong>
            <small>{busyLabel || "steady"}</small>
          </div>
          <div className="hero-card">
            <span>메모리</span>
            <strong>{formatNumber(status.memory_rss_mb)} MB</strong>
            <small>gallery {status.gallery_count || 0}명</small>
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="stage card">
          <div className="card-head">
            <div>
              <div className="card-eyebrow">Live Stream</div>
              <h2>실시간 인식 화면</h2>
            </div>
            <div className="status-row">
              <span className="pill">{formatNumber(status.capture_fps)} capture FPS</span>
              <span className="pill">{formatNumber(status.inference_fps)} infer FPS</span>
              <span className="pill">{formatNumber(status.stream_fps)} stream FPS</span>
            </div>
          </div>

          <div className="video-stage">
            <img className="video-feed" src="/stream.mjpg" alt="live stream" />
            <div className="overlay-layer">
              {status.latest_results?.map((result, index) => (
                <div
                  className={`overlay-box ${result.en_name === "Unknown" ? "unknown" : ""}`}
                  key={`${result.en_name}-${index}-${status.result_revision || 0}`}
                  style={buildBoxStyle(result, status)}
                >
                  <div className="overlay-label">
                    <strong>{overlayTitle(result)}</strong>
                    <span>{result.en_name}</span>
                    <small>sim {formatNumber(result.similarity)}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="stage-meta">
            <div>
              <span>카메라</span>
              <strong>{status.camera_source || "-"}</strong>
            </div>
            <div>
              <span>캡처 갱신</span>
              <strong>{status.last_frame_time || "-"}</strong>
            </div>
            <div>
              <span>결과 갱신</span>
              <strong>{status.last_result_time || "-"}</strong>
            </div>
            <div>
              <span>검출 수</span>
              <strong>{status.last_result_count || 0}</strong>
            </div>
          </div>

          <div className="telemetry-grid">
            <div>
              <span>최근 추론 시간</span>
              <strong>{formatNumber(status.last_inference_duration_ms)} ms</strong>
              <small>실제 한 번 처리에 걸린 시간</small>
            </div>
            <div>
              <span>평균 추론 시간</span>
              <strong>{formatNumber(status.avg_inference_duration_ms)} ms</strong>
              <small>지수 이동 평균 기준</small>
            </div>
            <div>
              <span>결과 revision</span>
              <strong>{status.result_revision || 0}</strong>
              <small>overlay와 결과 상태 동기화용</small>
            </div>
            <div>
              <span>목표 추론 상한</span>
              <strong>{status.max_inference_fps > 0 ? `${status.max_inference_fps} FPS` : "제한 없음"}</strong>
              <small>지금은 최신 프레임 우선 처리</small>
            </div>
          </div>
        </section>

        <aside className="sidebar">
          <section className="card">
            <div className="card-head compact">
              <div>
                <div className="card-eyebrow">Model Control</div>
                <h2>모델 전환</h2>
              </div>
            </div>
            <label className="field">
              <span>선택 모델</span>
              <select value={selectedModelPack} onChange={(event) => setSelectedModelPack(event.target.value)}>
                {status.available_model_packs?.map((item) => (
                  <option value={item.model_pack} key={item.model_pack}>
                    {item.model_pack}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary-button" onClick={handleSwitchModel} disabled={!selectedModelPack || !!busyLabel}>
              {busyLabel === "모델 전환 중" ? "전환 중..." : "모델 적용"}
            </button>
            <div className="info-grid compact-grid">
              <div>
                <span>resolved</span>
                <strong>{activePack?.resolved_model_pack || status.resolved_model_pack || "-"}</strong>
              </div>
              <div>
                <span>alias</span>
                <strong>{activePack?.alias_of || status.alias_of || "-"}</strong>
              </div>
            </div>
            {status.last_switch_summary?.duration_ms ? (
              <div className="soft-note">
                마지막 전환 {status.last_switch_summary.duration_ms} ms
                <br />
                {status.last_switch_summary.memory_before_mb} MB → {status.last_switch_summary.memory_after_mb} MB
                <br />
                모드: {status.last_switch_summary.switch_mode || "warm"}
              </div>
            ) : null}
          </section>

          <section className="card">
            <div className="card-head compact">
              <div>
                <div className="card-eyebrow">Live Health</div>
                <h2>실시간 상태</h2>
              </div>
            </div>
            <div className="info-grid health-grid">
              <div>
                <span>백엔드</span>
                <strong>{status.provider || "-"}</strong>
              </div>
              <div>
                <span>연결</span>
                <strong>{liveState}</strong>
              </div>
              <div>
                <span>갤러리 인원</span>
                <strong>{status.gallery_count || 0}</strong>
              </div>
              <div>
                <span>최근 오류</span>
                <strong>{statusMessage ? "있음" : "없음"}</strong>
              </div>
            </div>
          </section>
        </aside>

        <section className="gallery-workbench card">
          <div className="card-head">
            <div>
              <div className="card-eyebrow">Gallery Manager</div>
              <h2>저장된 인물 관리</h2>
            </div>
            <div className="status-row">
              {busyLabel ? <span className="pill warm">{busyLabel}</span> : null}
              {statusMessage ? <span className="pill danger">{statusMessage}</span> : null}
            </div>
          </div>

          <div className="gallery-layout">
            <div className="gallery-sidebar">
              <section className="subcard">
                <div className="subcard-head">
                  <div>
                    <div className="card-eyebrow">Create Profile</div>
                    <h3>새 프로필 추가</h3>
                  </div>
                </div>
                <p className="helper-text">
                  여기서는 인물 프로필만 먼저 만듭니다. 이미지는 오른쪽 편집 영역에서 촬영하거나 업로드합니다.
                </p>
                <form className="stack-form" onSubmit={handleCreatePerson}>
                  <label className="field">
                    <span>한글 이름</span>
                    <input
                      value={newPersonForm.name_ko}
                      onChange={(event) => setNewPersonForm((current) => ({ ...current, name_ko: event.target.value }))}
                      placeholder="예: 홍길동"
                    />
                  </label>
                  <label className="field">
                    <span>영문 이름</span>
                    <input
                      value={newPersonForm.name_en}
                      onChange={(event) => setNewPersonForm((current) => ({ ...current, name_en: event.target.value }))}
                      placeholder="예: GilDong"
                    />
                  </label>
                  <button className="primary-button" disabled={!!busyLabel}>
                    프로필 추가
                  </button>
                </form>
              </section>

              <section className="subcard">
                <div className="subcard-head">
                  <div>
                    <div className="card-eyebrow">Saved People</div>
                    <h3>갤러리 목록</h3>
                  </div>
                  <button className="secondary-button" onClick={() => refreshPeople()} disabled={!!busyLabel}>
                    새로고침
                  </button>
                </div>
                <p className="helper-text">선택한 인물의 이름 수정, 이미지 추가, 삭제는 오른쪽에서 처리합니다.</p>
                <div className="people-list">
                  {people.map((person) => (
                    <button
                      className={`person-chip ${person.person_id === selectedPersonId ? "active" : ""}`}
                      key={person.person_id}
                      onClick={() => setSelectedPersonId(person.person_id)}
                    >
                      <div className="person-chip-main">
                        <strong>{person.name_ko}</strong>
                        <span>{person.name_en || person.person_id}</span>
                      </div>
                      <small>{person.image_count} images</small>
                    </button>
                  ))}
                  {people.length === 0 ? <div className="empty-panel">아직 저장된 인물이 없습니다.</div> : null}
                </div>
              </section>
            </div>

            <section className="gallery-editor subcard">
              <div className="subcard-head">
                <div>
                  <div className="card-eyebrow">Selected Person</div>
                  <h3>{selectedPerson ? selectedPerson.name_ko : "선택된 인물 없음"}</h3>
                </div>
              </div>

              {selectedPerson ? (
                <>
                  <p className="helper-text">
                    이름 변경은 메타 정보만 수정합니다. 실제 등록 이미지는 아래 버튼으로 추가하거나 개별 삭제할 수 있습니다.
                  </p>

                  <div className="detail-grid">
                    <label className="field">
                      <span>한글 이름</span>
                      <input
                        value={editForm.name_ko}
                        onChange={(event) => setEditForm((current) => ({ ...current, name_ko: event.target.value }))}
                      />
                    </label>
                    <label className="field">
                      <span>영문 이름</span>
                      <input
                        value={editForm.name_en}
                        onChange={(event) => setEditForm((current) => ({ ...current, name_en: event.target.value }))}
                      />
                    </label>
                  </div>

                  <div className="action-row">
                    <button className="secondary-button" onClick={handleRenamePerson} disabled={!!busyLabel}>
                      이름 변경 저장
                    </button>
                    <button className="secondary-button" onClick={handleCaptureImage} disabled={!!busyLabel}>
                      현재 프레임으로 이미지 추가
                    </button>
                    <label className="upload-button">
                      파일 업로드
                      <input multiple type="file" accept="image/*" onChange={handleUploadImages} />
                    </label>
                    <button className="danger-button" onClick={handleDeletePerson} disabled={!!busyLabel}>
                      인물 전체 삭제
                    </button>
                  </div>

                  <div className="gallery-summary">
                    <div>
                      <span>프로필 ID</span>
                      <strong>{selectedPerson.person_id}</strong>
                    </div>
                    <div>
                      <span>등록 이미지</span>
                      <strong>{selectedPerson.images.length}</strong>
                    </div>
                    <div>
                      <span>마지막 갱신</span>
                      <strong>{selectedPerson.updated_at || "-"}</strong>
                    </div>
                  </div>

                  <div className="image-grid">
                    {selectedPerson.images.map((image) => (
                      <figure className="image-card" key={image.image_id}>
                        <img
                          src={`/api/gallery/people/${selectedPerson.person_id}/images/${image.image_id}/file`}
                          alt={image.filename}
                        />
                        <figcaption>
                          <span>{image.filename}</span>
                          <button onClick={() => handleDeleteImage(image.image_id)} disabled={!!busyLabel}>
                            삭제
                          </button>
                        </figcaption>
                      </figure>
                    ))}
                    {selectedPerson.images.length === 0 ? (
                      <div className="empty-panel">아직 등록된 이미지가 없습니다. 현재 프레임 저장이나 업로드를 눌러 추가하세요.</div>
                    ) : null}
                  </div>
                </>
              ) : (
                <div className="empty-panel">왼쪽 갤러리 목록에서 인물을 선택하거나 새 프로필을 추가하세요.</div>
              )}
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}
