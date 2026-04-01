import { useEffect, useMemo, useState } from "react";

const emptyStatus = {
  available_model_packs: [],
  latest_results: [],
  frame_width: 0,
  frame_height: 0,
  latest_results_count: 0,
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

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return Number(value).toFixed(2);
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

export default function App() {
  const [status, setStatus] = useState(emptyStatus);
  const [people, setPeople] = useState([]);
  const [selectedPersonId, setSelectedPersonId] = useState("");
  const [selectedModelPack, setSelectedModelPack] = useState("buffalo_m");
  const [newPersonForm, setNewPersonForm] = useState({ name_ko: "", name_en: "" });
  const [editForm, setEditForm] = useState({ name_ko: "", name_en: "" });
  const [busyLabel, setBusyLabel] = useState("");
  const [error, setError] = useState("");

  const selectedPerson = useMemo(
    () => people.find((person) => person.person_id === selectedPersonId) || null,
    [people, selectedPersonId],
  );

  async function refreshStatus() {
    try {
      const payload = await fetchJson("/api/status");
      setStatus(payload);
      setSelectedModelPack((current) => current || payload.model_pack || "buffalo_m");
    } catch (err) {
      setError(err.message);
    }
  }

  async function refreshPeople(preferredPersonId = null) {
    try {
      const payload = await fetchJson("/api/gallery/people");
      setPeople(payload.items);
      const firstPersonId = payload.items[0]?.person_id || "";
      setSelectedPersonId((current) => {
        const requested = preferredPersonId || current;
        if (requested && payload.items.some((person) => person.person_id === requested)) {
          return requested;
        }
        return firstPersonId;
      });
      const requestedPersonId = preferredPersonId || selectedPersonId || firstPersonId;
      const target = payload.items.find((person) => person.person_id === requestedPersonId)
        || payload.items[0];
      setEditForm({
        name_ko: target?.name_ko || "",
        name_en: target?.name_en || "",
      });
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refreshStatus();
    refreshPeople();
    const statusTimer = window.setInterval(refreshStatus, 1000);
    const peopleTimer = window.setInterval(() => refreshPeople(), 3000);
    return () => {
      window.clearInterval(statusTimer);
      window.clearInterval(peopleTimer);
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
  }, [selectedPersonId, selectedPerson]);

  async function withBusy(label, action) {
    setBusyLabel(label);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyLabel("");
      await refreshStatus();
      await refreshPeople(selectedPersonId);
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
    await withBusy("인물 생성 중", async () => {
      const payload = await fetchJson("/api/gallery/people", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newPersonForm),
      });
      setNewPersonForm({ name_ko: "", name_en: "" });
      setSelectedPersonId(payload.item.person_id);
      await refreshPeople(payload.item.person_id);
    });
  }

  async function handleRenamePerson() {
    if (!selectedPerson) {
      return;
    }
    await withBusy("이름 저장 중", async () => {
      await fetchJson(`/api/gallery/people/${selectedPerson.person_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
    });
  }

  async function handleDeletePerson() {
    if (!selectedPerson) {
      return;
    }
    if (!window.confirm(`${selectedPerson.name_ko} 인물을 삭제할까요?`)) {
      return;
    }
    await withBusy("인물 삭제 중", async () => {
      await fetchJson(`/api/gallery/people/${selectedPerson.person_id}`, {
        method: "DELETE",
      });
      setSelectedPersonId("");
    });
  }

  async function handleCaptureImage() {
    if (!selectedPerson) {
      return;
    }
    await withBusy("현재 프레임 저장 중", async () => {
      await fetchJson(`/api/gallery/people/${selectedPerson.person_id}/images/capture`, {
        method: "POST",
      });
    });
  }

  async function handleUploadImages(event) {
    if (!selectedPerson) {
      return;
    }
    const files = Array.from(event.target.files || []);
    if (files.length === 0) {
      return;
    }
    await withBusy("이미지 업로드 중", async () => {
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
    });
  }

  async function handleDeleteImage(imageId) {
    if (!selectedPerson) {
      return;
    }
    await withBusy("이미지 삭제 중", async () => {
      await fetchJson(`/api/gallery/people/${selectedPerson.person_id}/images/${imageId}`, {
        method: "DELETE",
      });
    });
  }

  const activePack = status.available_model_packs.find(
    (item) => item.model_pack === selectedModelPack,
  );

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <div className="eyebrow">InsightFace RKNN Console</div>
          <h1>OrangePI Face Runtime</h1>
          <p>
            RK3588에서 돌아가는 얼굴 인식 SDK와 운영용 웹 화면을 하나의 콘솔로 묶었습니다.
          </p>
        </div>
        <div className="hero-badges">
          <div className="hero-card">
            <span>현재 모델</span>
            <strong>{status.model_pack || "-"}</strong>
            <small>resolved: {status.resolved_model_pack || "-"}</small>
          </div>
          <div className="hero-card">
            <span>메모리</span>
            <strong>{formatNumber(status.memory_rss_mb)} MB</strong>
            <small>{busyLabel || "steady"}</small>
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
                  key={`${result.en_name}-${index}`}
                  style={buildBoxStyle(result, status)}
                >
                  <div className="overlay-label">
                    <strong>{result.kr_name}</strong>
                    <span>{result.en_name}</span>
                    <small>{formatNumber(result.similarity)}</small>
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
              <span>최근 프레임</span>
              <strong>{status.last_frame_time || "-"}</strong>
            </div>
            <div>
              <span>검출 수</span>
              <strong>{status.last_result_count || 0}</strong>
            </div>
            <div>
              <span>갤러리 인원</span>
              <strong>{status.gallery_count || 0}</strong>
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
            <div className="info-grid">
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
              </div>
            ) : null}
          </section>

          <section className="card">
            <div className="card-head compact">
              <div>
                <div className="card-eyebrow">Create Person</div>
                <h2>새 인물 등록</h2>
              </div>
            </div>
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
                인물 만들기
              </button>
            </form>
          </section>

          <section className="card gallery-card">
            <div className="card-head compact">
              <div>
                <div className="card-eyebrow">Gallery</div>
                <h2>등록 인물</h2>
              </div>
            </div>
            <div className="people-list">
              {people.map((person) => (
                <button
                  className={`person-chip ${person.person_id === selectedPersonId ? "active" : ""}`}
                  key={person.person_id}
                  onClick={() => setSelectedPersonId(person.person_id)}
                >
                  <strong>{person.name_ko}</strong>
                  <span>{person.name_en}</span>
                  <small>{person.image_count} images</small>
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="detail card">
          <div className="card-head">
            <div>
              <div className="card-eyebrow">Person Detail</div>
              <h2>이미지 관리</h2>
            </div>
            <div className="status-row">
              {busyLabel ? <span className="pill warm">{busyLabel}</span> : null}
              {error || status.last_error || status.last_switch_error ? (
                <span className="pill danger">{error || status.last_error || status.last_switch_error}</span>
              ) : null}
            </div>
          </div>

          {selectedPerson ? (
            <>
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
                  이름 저장
                </button>
                <button className="secondary-button" onClick={handleCaptureImage} disabled={!!busyLabel}>
                  현재 프레임 저장
                </button>
                <label className="upload-button">
                  이미지 업로드
                  <input multiple type="file" accept="image/*" onChange={handleUploadImages} />
                </label>
                <button className="danger-button" onClick={handleDeletePerson} disabled={!!busyLabel}>
                  인물 삭제
                </button>
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
                  <div className="empty-panel">아직 등록된 이미지가 없습니다.</div>
                ) : null}
              </div>
            </>
          ) : (
            <div className="empty-panel">왼쪽에서 인물을 선택하거나 새 인물을 만드세요.</div>
          )}
        </section>
      </main>
    </div>
  );
}
