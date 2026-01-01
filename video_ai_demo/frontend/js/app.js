// ========== 配置 ==========
const API_BASE_URL = 'http://localhost:8000';

// ========== 状态管理 ==========
const state = {
    mode: 'learn',
    targetFile: null,
    userFile: null,
    targetFileURL: null,
    currentJobId: null,
    analysisResult: null,
    zoom: 1,
    isPlaying: false,
    duration: 0
};

// ========== DOM元素 ==========
const elements = {
    // 模式切换
    navTabs: document.querySelectorAll('.nav-tab'),
    userVideoCard: document.getElementById('user-video-card'),
    
    // 文件上传
    targetUpload: document.getElementById('target-upload'),
    targetFile: document.getElementById('target-file'),
    userUpload: document.getElementById('user-upload'),
    userFile: document.getElementById('user-file'),
    
    // 选项
    fpsInput: document.getElementById('fps'),
    maxFramesInput: document.getElementById('max-frames'),
    showCamera: document.getElementById('show-camera'),
    showLighting: document.getElementById('show-lighting'),
    showColor: document.getElementById('show-color'),
    
    // 按钮
    btnAnalyze: document.getElementById('btn-analyze'),
    
    // 状态显示
    emptyState: document.getElementById('empty-state'),
    loadingState: document.getElementById('loading-state'),
    loadingProgress: document.getElementById('loading-progress'),
    progressFill: document.getElementById('progress-fill'),
    
    // 时间轴
    timelineContainer: document.getElementById('timeline-container'),
    timelineSubtitle: document.getElementById('timeline-subtitle'),
    timelineRuler: document.getElementById('timeline-ruler'),
    videoSegments: document.getElementById('video-segments'),
    cameraTrack: document.getElementById('camera-track'),
    lightingTrack: document.getElementById('lighting-track'),
    colorTrack: document.getElementById('color-track'),
    
    // 详情面板
    detailPanel: document.getElementById('detail-panel'),
    detailContent: document.getElementById('detail-content'),
    btnCloseDetail: document.getElementById('btn-close-detail')
};

// ========== 初始化 ==========
function init() {
    // 模式切换
    elements.navTabs.forEach(tab => {
        tab.addEventListener('click', () => handleModeSwitch(tab.dataset.mode));
    });
    
    // 文件上传
    setupFileUpload(elements.targetUpload, elements.targetFile, 'target');
    setupFileUpload(elements.userUpload, elements.userFile, 'user');
    
    // 开始分析按钮
    elements.btnAnalyze.addEventListener('click', handleAnalyze);
    
    // 详情面板关闭
    elements.btnCloseDetail.addEventListener('click', closeDetailPanel);
    
    // 导出按钮
    document.getElementById('btn-export').addEventListener('click', handleExport);
    
    // 缩放按钮
    document.getElementById('btn-zoom-in').addEventListener('click', () => handleZoom(1.2));
    document.getElementById('btn-zoom-out').addEventListener('click', () => handleZoom(0.8));
    
    // 播放控制
    setupVideoPlayer();
    
    // 轨道显示/隐藏控制
    setupTrackVisibility();
}

// ========== 模式切换 ==========
function handleModeSwitch(mode) {
    state.mode = mode;
    
    // 更新UI
    elements.navTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === mode);
    });
    
    // 显示/隐藏用户视频卡片
    elements.userVideoCard.style.display = mode === 'compare' ? 'block' : 'none';
    
    // 更新按钮状态
    updateAnalyzeButton();
}

// ========== 文件上传 ==========
function setupFileUpload(uploadArea, fileInput, type) {
    // 点击上传
    uploadArea.addEventListener('click', (e) => {
        if (!e.target.closest('.btn-remove')) {
            fileInput.click();
        }
    });
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file, type, uploadArea);
        }
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--color-primary)';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--color-border)';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--color-border)';
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('video/')) {
            handleFileSelect(file, type, uploadArea);
        }
    });
    
    // 移除文件
    const removeBtn = uploadArea.querySelector('.btn-remove');
    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            handleFileRemove(type, uploadArea, fileInput);
        });
    }
}

function handleFileSelect(file, type, uploadArea) {
    if (type === 'target') {
        state.targetFile = file;
        // 创建视频URL用于预览
        if (state.targetFileURL) {
            URL.revokeObjectURL(state.targetFileURL);
        }
        state.targetFileURL = URL.createObjectURL(file);
    } else {
        state.userFile = file;
    }
    
    // 更新UI
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    const fileInfo = uploadArea.querySelector('.file-info');
    const fileName = fileInfo.querySelector('.file-name');
    
    placeholder.style.display = 'none';
    fileInfo.style.display = 'flex';
    fileName.textContent = file.name;
    
    updateAnalyzeButton();
}

function handleFileRemove(type, uploadArea, fileInput) {
    if (type === 'target') {
        state.targetFile = null;
    } else {
        state.userFile = null;
    }
    
    fileInput.value = '';
    
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    const fileInfo = uploadArea.querySelector('.file-info');
    
    placeholder.style.display = 'block';
    fileInfo.style.display = 'none';
    
    updateAnalyzeButton();
}

function updateAnalyzeButton() {
    const canAnalyze = state.targetFile && 
        (state.mode === 'learn' || state.userFile);
    elements.btnAnalyze.disabled = !canAnalyze;
}

// ========== 开始分析 ==========
async function handleAnalyze() {
    showLoading();
    
    try {
        // 创建Job
        const jobId = await createJob();
        state.currentJobId = jobId;
        
        // 轮询状态
        await pollJobStatus(jobId);
        
    } catch (error) {
        console.error('分析失败:', error);
        alert('分析失败: ' + error.message);
        showEmpty();
    }
}

async function createJob() {
    const formData = {
        mode: state.mode,
        target_video: {
            source: {
                type: 'file',
                path: state.targetFile.path || `/Users/tang/Documents/${state.targetFile.name}`
            }
        },
        options: {
            scene_detection: {
                use_cv: true,
                threshold: 27.0,
                min_scene_len: 15
            },
            frame_extract: {
                fps: parseFloat(elements.fpsInput.value),
                max_frames: parseInt(elements.maxFramesInput.value)
            },
            llm: {
                enabled_modules: ['camera_motion', 'lighting', 'color_grading']
            }
        }
    };
    
    if (state.mode === 'compare' && state.userFile) {
        formData.user_video = {
            source: {
                type: 'file',
                path: state.userFile.path || `/Users/tang/Documents/${state.userFile.name}`
            }
        };
    }
    
    const response = await fetch(`${API_BASE_URL}/v1/video-analysis/jobs`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
        throw new Error('创建Job失败');
    }
    
    const data = await response.json();
    return data.job_id;
}

async function pollJobStatus(jobId) {
    const maxAttempts = 120; // 最多2分钟
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        const response = await fetch(`${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'succeeded') {
            state.analysisResult = data.result;
            showTimeline(data.result);
            return;
        } else if (data.status === 'failed') {
            throw new Error(data.error.message);
        } else if (data.status === 'running' && data.progress) {
            updateProgress(data.progress);
        }
        
        await sleep(1000);
        attempts++;
    }
    
    throw new Error('分析超时');
}

function updateProgress(progress) {
    const percent = progress.percent || 0;
    const message = progress.message || '处理中...';
    const stage = progress.stage || '';
    
    elements.loadingProgress.textContent = `${stage} ${Math.round(percent)}%`;
    elements.progressFill.style.width = `${percent}%`;
}

// ========== 显示时间轴 ==========
function showTimeline(result) {
    elements.emptyState.style.display = 'none';
    elements.loadingState.style.display = 'none';
    elements.timelineContainer.style.display = 'flex';
    
    const segments = result.target?.segments || [];
    const totalDuration = segments.length > 0 
        ? segments[segments.length - 1].end_ms 
        : 0;
    
    state.duration = totalDuration;
    
    // 更新标题
    elements.timelineSubtitle.textContent = 
        `${segments.length}个镜头 · ${(totalDuration / 1000).toFixed(1)}秒`;
    
    // 加载视频到预览轨道
    loadVideoPreview();
    
    // 渲染时间标尺
    renderTimeRuler(totalDuration);
    
    // 渲染所有轨道（不管复选框状态，始终渲染）
    renderVideoSegments(segments, totalDuration);
    renderFeatureTrack(segments, totalDuration, 'camera_motion', elements.cameraTrack);
    renderFeatureTrack(segments, totalDuration, 'lighting', elements.lightingTrack);
    renderFeatureTrack(segments, totalDuration, 'color_grading', elements.colorTrack);
    
    // 根据复选框状态显示/隐藏轨道
    updateTrackVisibility();
}

function renderTimeRuler(totalDuration) {
    const ruler = elements.timelineRuler;
    ruler.innerHTML = '';
    
    const intervals = 10;
    for (let i = 0; i <= intervals; i++) {
        const time = (totalDuration / intervals) * i;
        const mark = document.createElement('div');
        mark.style.position = 'absolute';
        mark.style.left = `${(i / intervals) * 100}%`;
        mark.style.height = '100%';
        mark.style.borderLeft = '1px solid var(--color-border)';
        mark.style.fontSize = '11px';
        mark.style.paddingLeft = '4px';
        mark.style.paddingTop = '4px';
        mark.style.color = 'var(--color-text-secondary)';
        mark.textContent = formatTime(time);
        ruler.appendChild(mark);
    }
}

function renderVideoSegments(segments, totalDuration) {
    const container = elements.videoSegments;
    container.innerHTML = '';
    
    segments.forEach(segment => {
        const div = createSegmentElement(
            segment,
            totalDuration,
            'video',
            segment.segment_id,
            `${(segment.duration_ms / 1000).toFixed(1)}s`
        );
        container.appendChild(div);
    });
}

function renderFeatureTrack(segments, totalDuration, category, container) {
    container.innerHTML = '';
    
    segments.forEach(segment => {
        const features = segment.features.filter(f => f.category === category);
        
        features.forEach(feature => {
            const div = createSegmentElement(
                segment,
                totalDuration,
                getCategoryClass(category),
                feature.type,
                feature.value,
                feature.confidence
            );
            
            div.addEventListener('click', () => showFeatureDetail(feature, segment));
            container.appendChild(div);
        });
    });
}

function createSegmentElement(segment, totalDuration, className, label, value, confidence = null) {
    const div = document.createElement('div');
    div.className = `segment segment-${className}`;
    
    const left = (segment.start_ms / totalDuration) * 100;
    const width = (segment.duration_ms / totalDuration) * 100;
    
    div.style.left = `${left}%`;
    div.style.width = `${width}%`;
    
    div.innerHTML = `
        <div class="segment-content">
            <div class="segment-label">${label}</div>
            <div class="segment-value">${value}</div>
            ${confidence ? `<div class="segment-confidence">${(confidence * 100).toFixed(0)}%</div>` : ''}
        </div>
    `;
    
    return div;
}

function getCategoryClass(category) {
    const map = {
        'camera_motion': 'camera',
        'lighting': 'lighting',
        'color_grading': 'color'
    };
    return map[category] || 'camera';
}

// ========== 详情面板 ==========
function showFeatureDetail(feature, segment) {
    elements.detailPanel.classList.add('open');
    
    elements.detailContent.innerHTML = `
        <div style="margin-bottom: 16px;">
            <div style="font-size: 13px; color: var(--color-text-secondary); margin-bottom: 4px;">类别</div>
            <div style="font-size: 16px; font-weight: 600;">${getCategoryName(feature.category)}</div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <div style="font-size: 13px; color: var(--color-text-secondary); margin-bottom: 4px;">类型</div>
            <div style="font-size: 16px; font-weight: 600;">${feature.type}</div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <div style="font-size: 13px; color: var(--color-text-secondary); margin-bottom: 4px;">描述</div>
            <div style="font-size: 16px; font-weight: 600;">${feature.value}</div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <div style="font-size: 13px; color: var(--color-text-secondary); margin-bottom: 4px;">置信度</div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="flex: 1; height: 6px; background: var(--color-surface); border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: ${feature.confidence * 100}%; background: var(--color-primary);"></div>
                </div>
                <div style="font-size: 16px; font-weight: 600;">${(feature.confidence * 100).toFixed(0)}%</div>
            </div>
        </div>
        
        <div>
            <div style="font-size: 13px; color: var(--color-text-secondary); margin-bottom: 4px;">时间范围</div>
            <div style="font-size: 16px; font-weight: 600;">
                ${formatTime(segment.start_ms)} - ${formatTime(segment.end_ms)}
            </div>
        </div>
    `;
}

function closeDetailPanel() {
    elements.detailPanel.classList.remove('open');
}

function getCategoryName(category) {
    const names = {
        'camera_motion': '运镜',
        'lighting': '光线',
        'color_grading': '调色'
    };
    return names[category] || category;
}

// ========== 导出结果 ==========
function handleExport() {
    if (!state.analysisResult) return;
    
    const dataStr = JSON.stringify(state.analysisResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analysis_${state.currentJobId}.json`;
    link.click();
}

// ========== 缩放 ==========
function handleZoom(factor) {
    state.zoom *= factor;
    state.zoom = Math.max(0.5, Math.min(state.zoom, 3));
    // TODO: 实现时间轴缩放
}

// ========== 工具函数 ==========
function showEmpty() {
    elements.emptyState.style.display = 'flex';
    elements.loadingState.style.display = 'none';
    elements.timelineContainer.style.display = 'none';
}

function showLoading() {
    elements.emptyState.style.display = 'none';
    elements.loadingState.style.display = 'flex';
    elements.timelineContainer.style.display = 'none';
    elements.progressFill.style.width = '0%';
}

function formatTime(ms) {
    const seconds = ms / 1000;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 1000);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ========== 视频播放器 ==========
function setupVideoPlayer() {
    const video = document.getElementById('preview-video');
    const btnPlay = document.getElementById('btn-play');
    const timeDisplay = document.getElementById('time-display');
    const timeTotal = document.getElementById('time-total');
    const playbackSlider = document.getElementById('playback-slider');
    const playbackProgress = document.getElementById('playback-progress');
    const playbackHandle = document.getElementById('playback-handle');
    const playhead = document.getElementById('playhead');
    const btnFullscreen = document.getElementById('btn-fullscreen');
    const btnToggleVideo = document.getElementById('btn-toggle-video');
    const videoPreviewContent = document.getElementById('video-preview-content');
    
    // 播放/暂停
    btnPlay.addEventListener('click', () => {
        if (video.paused) {
            video.play();
            btnPlay.textContent = '⏸';
            state.isPlaying = true;
        } else {
            video.pause();
            btnPlay.textContent = '▶';
            state.isPlaying = false;
        }
    });
    
    // 视频时间更新
    video.addEventListener('timeupdate', () => {
        const currentTime = video.currentTime * 1000; // 转换为毫秒
        const duration = video.duration * 1000;
        
        // 更新时间显示
        timeDisplay.textContent = formatTime(currentTime);
        
        // 更新进度条
        const progress = (currentTime / duration) * 100;
        playbackProgress.style.width = `${progress}%`;
        playbackHandle.style.left = `${progress}%`;
        
        // 更新播放头
        if (playhead) {
            playhead.style.left = `${progress}%`;
        }
    });
    
    // 视频加载完成
    video.addEventListener('loadedmetadata', () => {
        const duration = video.duration * 1000;
        timeTotal.textContent = formatTime(duration);
        state.duration = duration;
    });
    
    // 视频结束
    video.addEventListener('ended', () => {
        btnPlay.textContent = '▶';
        state.isPlaying = false;
    });
    
    // 进度条点击
    playbackSlider.addEventListener('click', (e) => {
        const rect = playbackSlider.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        video.currentTime = (video.duration * percent);
    });
    
    // 进度条拖拽
    let isDragging = false;
    playbackHandle.addEventListener('mousedown', (e) => {
        isDragging = true;
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const rect = playbackSlider.getBoundingClientRect();
        let percent = (e.clientX - rect.left) / rect.width;
        percent = Math.max(0, Math.min(1, percent));
        
        video.currentTime = video.duration * percent;
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
    
    // 全屏
    btnFullscreen.addEventListener('click', () => {
        if (video.requestFullscreen) {
            video.requestFullscreen();
        } else if (video.webkitRequestFullscreen) {
            video.webkitRequestFullscreen();
        }
    });
    
    // 显示/隐藏视频
    btnToggleVideo.addEventListener('click', () => {
        if (videoPreviewContent.style.display === 'none') {
            videoPreviewContent.style.display = 'flex';
            btnToggleVideo.textContent = '👁️';
        } else {
            videoPreviewContent.style.display = 'none';
            btnToggleVideo.textContent = '👁️‍🗨️';
        }
    });
    
    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        switch(e.code) {
            case 'Space':
                e.preventDefault();
                btnPlay.click();
                break;
            case 'ArrowLeft':
                video.currentTime = Math.max(0, video.currentTime - 1);
                break;
            case 'ArrowRight':
                video.currentTime = Math.min(video.duration, video.currentTime + 1);
                break;
            case 'KeyF':
                btnFullscreen.click();
                break;
        }
    });
}

function loadVideoPreview() {
    const video = document.getElementById('preview-video');
    if (state.targetFileURL) {
        video.src = state.targetFileURL;
        video.load();
    }
}

// ========== 轨道显示控制 ==========
function setupTrackVisibility() {
    // 为每个复选框添加事件监听
    elements.showCamera.addEventListener('change', updateTrackVisibility);
    elements.showLighting.addEventListener('change', updateTrackVisibility);
    elements.showColor.addEventListener('change', updateTrackVisibility);
    
    // 注意：不在这里调用 updateTrackVisibility()
    // 因为轨道还没有渲染，会在 showTimeline() 中调用
}

function updateTrackVisibility() {
    // 获取轨道元素（.track）
    const cameraTrack = elements.cameraTrack.closest('.track');
    const lightingTrack = elements.lightingTrack.closest('.track');
    const colorTrack = elements.colorTrack.closest('.track');
    
    // 根据复选框状态显示/隐藏轨道
    if (cameraTrack) {
        cameraTrack.style.display = elements.showCamera.checked ? 'flex' : 'none';
    }
    if (lightingTrack) {
        lightingTrack.style.display = elements.showLighting.checked ? 'flex' : 'none';
    }
    if (colorTrack) {
        colorTrack.style.display = elements.showColor.checked ? 'flex' : 'none';
    }
    
    console.log('轨道显示状态更新:', {
        camera: elements.showCamera.checked,
        lighting: elements.showLighting.checked,
        color: elements.showColor.checked
    });
}

// ========== 启动 ==========
init();

