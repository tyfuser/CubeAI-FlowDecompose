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
    duration: 0,
    isStreaming: false,
    streamingSegments: [],
    historyList: []
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
    
    // 测试播放头按钮
    const btnTestPlayhead = document.getElementById('btn-test-playhead');
    if (btnTestPlayhead) {
        btnTestPlayhead.addEventListener('click', () => {
            updatePlayheadPosition(50); // 测试50%位置
            alert('播放头已设置到50%位置，请检查轨道区域是否可见红色竖线');
        });
    }
    
    // 缩放按钮
    document.getElementById('btn-zoom-in').addEventListener('click', () => handleZoom(1.2));
    document.getElementById('btn-zoom-out').addEventListener('click', () => handleZoom(0.8));
    
    // 播放控制
    setupVideoPlayer();
    
    // 轨道显示/隐藏控制
    setupTrackVisibility();
    
    // 时间标尺点击跳转
    setupTimelineRulerClick();
    
    // 监听窗口调整大小，更新播放头位置
    window.addEventListener('resize', () => {
        const video = document.getElementById('preview-video');
        if (video && video.duration) {
            const currentTime = video.currentTime * 1000;
            const duration = video.duration * 1000;
            const progress = (currentTime / duration) * 100;
            updatePlayheadPosition(progress);
        }
    });
}

// ========== 模式切换 ==========
function handleModeSwitch(mode) {
    const previousMode = state.mode;
    state.mode = mode;
    
    // 更新UI
    elements.navTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === mode);
    });
    
    // 根据模式显示不同界面
    if (mode === 'learn') {
        // 如果从 history 切换回 learn，恢复界面
        if (previousMode === 'history') {
            document.querySelector('.sidebar').style.display = 'block';
            
            // 重建 Learn 界面结构
            restoreLearnView();
        }
        updateAnalyzeButton();
    } else if (mode === 'history') {
        // 显示History界面（不影响后台运行的任务）
        showHistoryView();
    }
}

// ========== 恢复 Learn 界面 ==========
function restoreLearnView() {
    const mainContent = document.querySelector('.main-content');
    
    // 重建完整的Learn界面结构
    mainContent.innerHTML = `
        <div id="empty-state" class="empty-state" style="display: none;">
            <div class="empty-icon">🎬</div>
            <div class="empty-title">开始分析你的视频</div>
            <div class="empty-text">上传视频，AI 将自动拆解镜头并分析特征</div>
        </div>
        
        <div id="loading-state" class="loading-state" style="display: none;">
            <div class="loading-spinner"></div>
            <div class="loading-title">分析中...</div>
            <div class="loading-text">这可能需要几分钟</div>
            <div id="loading-progress" class="loading-text"></div>
            <div class="progress-bar">
                <div id="progress-fill" class="progress-fill"></div>
            </div>
        </div>
        
        <div id="timeline-container" class="timeline-container" style="display: none;">
            <div class="timeline-header">
                <div>
                    <h2 class="timeline-title">
                        时间轴
                        <span id="timeline-subtitle" class="timeline-subtitle"></span>
                    </h2>
                </div>
                <div class="timeline-controls">
                    <button id="btn-zoom-in" class="btn-secondary">🔍+</button>
                    <button id="btn-zoom-out" class="btn-secondary">🔍-</button>
                    <button id="btn-export" class="btn-secondary">💾 导出</button>
                </div>
            </div>
            
            <div class="fixed-track">
                <div class="video-preview-track">
                    <div id="video-preview-content" class="video-preview-content">
                        <video id="preview-video" class="preview-video"></video>
                    </div>
                </div>
                
                <div class="playback-controls">
                    <button id="btn-play" class="btn-play">▶</button>
                    <div id="time-display" class="time-display">00:00.000</div>
                    <div id="playback-slider" class="playback-slider">
                        <div id="playback-progress" class="playback-progress"></div>
                        <div id="playback-handle" class="playback-handle"></div>
                    </div>
                    <div id="time-total" class="time-display">00:00.000</div>
                    <button id="btn-fullscreen" class="btn-secondary btn-small">⛶</button>
                    <button id="btn-toggle-video" class="btn-secondary btn-small">👁️</button>
                </div>
            </div>
            
            <div id="timeline-ruler" class="timeline-ruler"></div>
            
            <div id="tracks-container" class="tracks-container">
                <div id="playhead" class="playhead" style="display: none;"></div>
                
                <div class="track">
                    <div class="track-header">
                        <span class="track-icon">🎬</span>
                        <span class="track-name">视频片段</span>
                    </div>
                    <div id="video-segments" class="track-content"></div>
                </div>
                
                <div class="track">
                    <div class="track-header">
                        <span class="track-icon">📹</span>
                        <span class="track-name">运镜</span>
                    </div>
                    <div id="camera-track" class="track-content"></div>
                </div>
                
                <div class="track">
                    <div class="track-header">
                        <span class="track-icon">💡</span>
                        <span class="track-name">光线</span>
                    </div>
                    <div id="lighting-track" class="track-content"></div>
                </div>
                
                <div class="track">
                    <div class="track-header">
                        <span class="track-icon">🎨</span>
                        <span class="track-name">调色</span>
                    </div>
                    <div id="color-track" class="track-content"></div>
                </div>
            </div>
        </div>
        
        <!-- 详情面板 -->
        <div class="detail-panel" id="detail-panel">
            <div class="detail-header">
                <h3 class="detail-title">镜头详细分析</h3>
                <button class="btn-close" id="btn-close-detail">×</button>
            </div>
            <div class="detail-content" id="detail-content">
                <div class="detail-loading">加载中...</div>
            </div>
        </div>
    `;
    
    // 重新初始化所有元素引用
    elements.emptyState = document.getElementById('empty-state');
    elements.loadingState = document.getElementById('loading-state');
    elements.loadingProgress = document.getElementById('loading-progress');
    elements.progressFill = document.getElementById('progress-fill');
    elements.timelineContainer = document.getElementById('timeline-container');
    elements.timelineSubtitle = document.getElementById('timeline-subtitle');
    elements.timelineRuler = document.getElementById('timeline-ruler');
    elements.videoSegments = document.getElementById('video-segments');
    elements.cameraTrack = document.getElementById('camera-track');
    elements.lightingTrack = document.getElementById('lighting-track');
    elements.colorTrack = document.getElementById('color-track');
    
    // 确保详情面板引用也存在（虽然它不在main-content里，但保险起见）
    elements.detailPanel = document.getElementById('detail-panel');
    elements.detailContent = document.getElementById('detail-content');
    elements.btnCloseDetail = document.getElementById('btn-close-detail');
    
    // 重新绑定详情面板关闭按钮
    if (elements.btnCloseDetail) {
        elements.btnCloseDetail.addEventListener('click', closeDetailPanel);
    }
    
    // 重新初始化视频播放器
    setupVideoPlayer();
    
    // 重新初始化时间标尺点击
    setupTimelineRulerClick();
    
    // 重新初始化轨道显示控制
    setupTrackVisibility();
    
    // 重新绑定按钮事件
    const btnExport = document.getElementById('btn-export');
    const btnZoomIn = document.getElementById('btn-zoom-in');
    const btnZoomOut = document.getElementById('btn-zoom-out');
    
    if (btnExport) btnExport.addEventListener('click', handleExport);
    if (btnZoomIn) btnZoomIn.addEventListener('click', () => handleZoom(1.2));
    if (btnZoomOut) btnZoomOut.addEventListener('click', () => handleZoom(0.8));
    
    // 根据状态显示对应界面
    if (state.analysisResult) {
        // 如果有分析结果，显示时间轴
        console.log('恢复之前的分析结果显示，segments数量:', state.analysisResult.target?.segments?.length);
        showTimeline(state.analysisResult, false);
        console.log('showTimeline 调用完成');
    } else if (state.currentJobId) {
        // 如果有当前任务ID，可能正在运行
        console.log('有正在运行的任务，显示加载状态');
        showLoading();
    } else {
        // 否则显示空状态
        console.log('显示空状态');
        showEmpty();
    }
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
    let hasShownInitialTimeline = false;
    
    while (attempts < maxAttempts) {
        const response = await fetch(`${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'succeeded') {
            state.analysisResult = data.result;
            showTimeline(data.result, false); // 最终结果，不显示加载动画
            return;
        } else if (data.status === 'failed') {
            throw new Error(data.error.message);
        } else if (data.status === 'running') {
            updateProgress(data.progress);
            
            // 如果有部分结果，实时显示
            if (data.partial_result) {
                if (!hasShownInitialTimeline) {
                    // 第一次显示时间轴
                    showTimeline(data.partial_result, true); // 显示加载动画
                    hasShownInitialTimeline = true;
                } else {
                    // 更新已有的时间轴
                    updateTimeline(data.partial_result);
                }
            }
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
function showTimeline(result, isStreaming = false) {
    elements.emptyState.style.display = 'none';
    elements.loadingState.style.display = 'none';
    elements.timelineContainer.style.display = 'flex';
    
    const segments = result.target?.segments || [];
    const totalDuration = segments.length > 0 
        ? segments[segments.length - 1].end_ms 
        : 0;
    
    state.duration = totalDuration;
    state.isStreaming = isStreaming;
    state.streamingSegments = segments;
    
    // 更新标题
    const analyzingText = isStreaming ? ' (分析中...)' : '';
    elements.timelineSubtitle.textContent = 
        `${segments.length}个镜头 · ${(totalDuration / 1000).toFixed(1)}秒${analyzingText}`;
    
    // 加载视频到预览轨道
    loadVideoPreview();
    
    // 渲染时间标尺
    renderTimeRuler(totalDuration);
    
    // 渲染所有轨道（带加载状态）
    renderVideoSegments(segments, totalDuration, isStreaming);
    renderFeatureTrack(segments, totalDuration, 'camera_motion', elements.cameraTrack, isStreaming);
    renderFeatureTrack(segments, totalDuration, 'lighting', elements.lightingTrack, isStreaming);
    renderFeatureTrack(segments, totalDuration, 'color_grading', elements.colorTrack, isStreaming);
    
    // 根据复选框状态显示/隐藏轨道
    updateTrackVisibility();
    
    // 显示测试按钮
    const btnTestPlayhead = document.getElementById('btn-test-playhead');
    if (btnTestPlayhead) {
        btnTestPlayhead.style.display = 'inline-block';
    }
}

// ========== 更新时间轴 ==========
function updateTimeline(result) {
    const segments = result.target?.segments || [];
    const totalDuration = segments.length > 0 
        ? segments[segments.length - 1].end_ms 
        : 0;
    
    const isAnalyzing = result.target?.analyzing || false;
    state.isStreaming = isAnalyzing;
    state.streamingSegments = segments;
    
    // 更新标题
    const analyzingText = isAnalyzing ? ' (分析中...)' : '';
    elements.timelineSubtitle.textContent = 
        `${segments.length}个镜头 · ${(totalDuration / 1000).toFixed(1)}秒${analyzingText}`;
    
    // 更新轨道内容
    renderVideoSegments(segments, totalDuration, isAnalyzing);
    renderFeatureTrack(segments, totalDuration, 'camera_motion', elements.cameraTrack, isAnalyzing);
    renderFeatureTrack(segments, totalDuration, 'lighting', elements.lightingTrack, isAnalyzing);
    renderFeatureTrack(segments, totalDuration, 'color_grading', elements.colorTrack, isAnalyzing);
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

function renderVideoSegments(segments, totalDuration, isStreaming = false) {
    const container = elements.videoSegments;
    if (!container) {
        console.error('videoSegments 容器未找到！');
        return;
    }
    
    container.innerHTML = '';
    console.log('renderVideoSegments: 渲染', segments.length, '个片段');
    
    segments.forEach((segment, index) => {
        const analyzing = segment.analyzing || false;
        const div = createSegmentElement(
            segment,
            totalDuration,
            'video',
            segment.segment_id,
            `${(segment.duration_ms / 1000).toFixed(1)}s`,
            null,
            analyzing
        );
        
        // 点击视频segment显示完整分析
        if (!analyzing) {
            // 添加测试属性
            div.setAttribute('data-segment-id', segment.segment_id);
            div.setAttribute('data-clickable', 'true');
            
            div.addEventListener('click', (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                console.log('🎬 片段被点击！segment:', segment.segment_id);
                console.log('事件对象:', e);
                console.log('当前目标:', e.currentTarget);
                showSegmentDetail(segment);
            });
            
            // 添加 mouseenter 测试
            div.addEventListener('mouseenter', () => {
                console.log('鼠标进入片段:', segment.segment_id);
            });
            
            console.log(`✓ 已为 segment ${segment.segment_id} (索引${index}) 添加点击事件`);
        }
        
        container.appendChild(div);
    });
    
    console.log(`✓ 共渲染 ${segments.length} 个视频片段，容器内元素数: ${container.children.length}`);
}

function renderFeatureTrack(segments, totalDuration, category, container, isStreaming = false) {
    container.innerHTML = '';
    
    segments.forEach((segment, segIndex) => {
        const analyzing = segment.analyzing || false;
        const features = segment.features.filter(f => f.category === category);
        
        if (features.length > 0) {
            features.forEach((feature, featIndex) => {
                const div = createSegmentElement(
                    segment,
                    totalDuration,
                    getCategoryClass(category),
                    feature.type,
                    feature.value,
                    feature.confidence,
                    false
                );
                
                // 添加测试属性
                div.setAttribute('data-segment-id', segment.segment_id);
                div.setAttribute('data-feature-type', feature.type);
                div.setAttribute('data-category', category);
                div.setAttribute('data-clickable', 'true');
                
                div.addEventListener('click', (e) => {
                    e.stopPropagation(); // 阻止事件冒泡
                    console.log(`🎨 特征片段被点击！category: ${category}, type: ${feature.type}, segment: ${segment.segment_id}`);
                    console.log('事件对象:', e);
                    console.log('当前目标:', e.currentTarget);
                    showFeatureDetail(feature, segment);
                });
                
                // 添加 mouseenter 测试
                div.addEventListener('mouseenter', () => {
                    console.log(`鼠标进入特征片段: ${category} - ${feature.type} (seg${segIndex}-feat${featIndex})`);
                });
                
                console.log(`✓ 已为 ${category} feature ${feature.type} (seg${segIndex}-feat${featIndex}) 添加点击事件`);
                
                container.appendChild(div);
            });
        } else if (analyzing) {
            // 显示加载占位符
            const div = createSegmentElement(
                segment,
                totalDuration,
                getCategoryClass(category) + ' analyzing',
                'analyzing',
                '分析中...',
                null,
                true
            );
            container.appendChild(div);
        }
    });
    
    console.log(`✓ 共渲染 ${category} 轨道，容器内元素数: ${container.children.length}`);
}

function createSegmentElement(segment, totalDuration, className, label, value, confidence = null, analyzing = false) {
    const div = document.createElement('div');
    div.className = `segment segment-${className}${analyzing ? ' segment-analyzing' : ''}`;
    
    const left = (segment.start_ms / totalDuration) * 100;
    const width = (segment.duration_ms / totalDuration) * 100;
    
    div.style.left = `${left}%`;
    div.style.width = `${width}%`;
    
    if (analyzing) {
        div.innerHTML = `
            <div class="segment-content">
                <div class="segment-value">
                    <span class="loading-spinner"></span>
                    ${value}
                </div>
            </div>
        `;
    } else {
        div.innerHTML = `
            <div class="segment-content">
                <div class="segment-label">${label}</div>
                <div class="segment-value">${value}</div>
                ${confidence ? `<div class="segment-confidence">${(confidence * 100).toFixed(0)}%</div>` : ''}
            </div>
        `;
    }
    
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
function showSegmentDetail(segment) {
    console.log('showSegmentDetail 被调用:', segment);
    console.log('elements.detailPanel:', elements.detailPanel);
    console.log('document.getElementById("detail-panel"):', document.getElementById('detail-panel'));
    
    // 确保获取最新的元素引用
    const detailPanel = document.getElementById('detail-panel');
    const detailContent = document.getElementById('detail-content');
    
    if (!detailPanel) {
        console.error('detailPanel 元素未找到！');
        return;
    }
    
    console.log('detailPanel 找到了，准备打开');
    detailPanel.classList.add('open');
    console.log('detailPanel.classList:', detailPanel.classList);
    
    // 聚焦到该segment
    focusOnSegment(segment);
    
    // 构建详细内容
    const cameraFeatures = segment.features?.filter(f => f.category === 'camera_motion') || [];
    const lightingFeatures = segment.features?.filter(f => f.category === 'lighting') || [];
    const colorFeatures = segment.features?.filter(f => f.category === 'color_grading') || [];
    
    console.log('特征数量:', {camera: cameraFeatures.length, lighting: lightingFeatures.length, color: colorFeatures.length});
    
    try {
        detailContent.innerHTML = `
            <div class="detail-section">
                <h4 class="section-title">📹 镜头信息</h4>
                <div class="info-item">
                    <span class="info-label">片段ID</span>
                    <span class="info-value">${segment.segment_id}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">时间范围</span>
                    <span class="info-value">${formatTime(segment.start_ms)} - ${formatTime(segment.end_ms)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">时长</span>
                    <span class="info-value">${(segment.duration_ms / 1000).toFixed(2)}秒</span>
                </div>
            </div>
            
            ${cameraFeatures.length > 0 ? renderCameraAnalysis(cameraFeatures) : '<div class="detail-section"><p>无运镜特征</p></div>'}
            ${lightingFeatures.length > 0 ? renderLightingAnalysis(lightingFeatures) : '<div class="detail-section"><p>无光线特征</p></div>'}
            ${colorFeatures.length > 0 ? renderColorAnalysis(colorFeatures) : '<div class="detail-section"><p>无调色特征</p></div>'}
        `;
        console.log('详情内容已更新');
    } catch (error) {
        console.error('渲染详情内容时出错:', error);
        detailContent.innerHTML = `
            <div class="detail-section">
                <p>加载详情时出错: ${error.message}</p>
            </div>
        `;
    }
}

function showFeatureDetail(feature, segment) {
    console.log('showFeatureDetail 被调用:', feature, segment);
    
    // 确保获取最新的元素引用
    const detailPanel = document.getElementById('detail-panel');
    const detailContent = document.getElementById('detail-content');
    
    if (!detailPanel) {
        console.error('detailPanel 元素未找到！');
        return;
    }
    
    detailPanel.classList.add('open');
    
    // 聚焦到该segment
    focusOnSegment(segment);
    
    detailContent.innerHTML = `
        <div class="detail-section">
            <h4 class="section-title">📹 镜头信息</h4>
            <div class="info-item">
                <span class="info-label">片段ID</span>
                <span class="info-value">${segment.segment_id}</span>
            </div>
            <div class="info-item">
                <span class="info-label">时间范围</span>
                <span class="info-value">${formatTime(segment.start_ms)} - ${formatTime(segment.end_ms)}</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h4 class="section-title">${getCategoryIcon(feature.category)} ${getCategoryName(feature.category)}特征</h4>
            ${renderFeatureDetail(feature)}
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

function getCategoryIcon(category) {
    const icons = {
        'camera_motion': '📹',
        'lighting': '💡',
        'color_grading': '🎨'
    };
    return icons[category] || '📌';
}

function focusOnSegment(segment) {
    // 让视频跳转到该segment的起始时间
    const video = document.getElementById('preview-video');
    if (video && video.duration) {
        video.currentTime = segment.start_ms / 1000;
        updatePlayheadPosition((segment.start_ms / state.duration) * 100);
    }
}

function renderCameraAnalysis(features) {
    console.log('renderCameraAnalysis 调用，特征数量:', features.length);
    
    let html = '<div class="detail-section"><h4 class="section-title">📹 运镜分析</h4>';
    
    features.forEach(f => {
        const detailed = f.detailed_description || {};
        
        html += `
            <div class="feature-card">
                <div class="feature-header">
                    <span class="feature-badge">${f.value}</span>
                    <span class="confidence-badge">${(f.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="feature-body">
                    ${detailed.summary ? `
                        <div class="feature-summary">${detailed.summary}</div>
                    ` : ''}
                    
                    ${detailed.technical_terms && detailed.technical_terms.length > 0 ? `
                        <div class="feature-terms">
                            <div class="terms-label">专业术语：</div>
                            <div class="terms-list">
                                ${detailed.technical_terms.map(term => `<span class="term-badge">${term}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${detailed.purpose ? `
                        <div class="feature-meaning">
                            <strong>镜头意义：</strong>${detailed.purpose}
                        </div>
                    ` : (typeof getMovementMeaning === 'function' ? `
                        <div class="feature-meaning">
                            ${getMovementMeaning(f.type) || ''}
                        </div>
                    ` : '')}
                    
                    ${detailed.parameters && Object.keys(detailed.parameters).length > 0 ? `
                        <div class="feature-params">
                            <div class="params-label">技术参数：</div>
                            ${Object.entries(detailed.parameters).map(([key, val]) => `
                                <div class="param-item">
                                    <span class="param-key">${key}:</span>
                                    <span class="param-value">${val}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function renderLightingAnalysis(features) {
    console.log('renderLightingAnalysis 调用，特征数量:', features.length);
    
    if (features.length === 0) {
        return '<div class="detail-section"><h4 class="section-title">💡 光线分析</h4><p>无光线特征</p></div>';
    }
    
    let html = '<div class="detail-section"><h4 class="section-title">💡 光线分析</h4>';
    
    features.forEach(f => {
        const detailed = f.detailed_description || {};
        
        html += `
            <div class="feature-card">
                <div class="feature-header">
                    <span class="feature-badge">${f.value}</span>
                    <span class="confidence-badge">${(f.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="feature-body">
                    ${detailed.summary ? `
                        <div class="feature-summary">${detailed.summary}</div>
                    ` : ''}
                    
                    ${detailed.technical_terms && detailed.technical_terms.length > 0 ? `
                        <div class="feature-terms">
                            <div class="terms-label">专业术语：</div>
                            <div class="terms-list">
                                ${detailed.technical_terms.map(term => `<span class="term-badge">${term}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${detailed.diagram ? `
                        <div class="lighting-diagram">
                            <div class="diagram-label">光路图：</div>
                            <div class="diagram-content">${detailed.diagram}</div>
                        </div>
                    ` : (typeof getLightingDiagram === 'function' ? getLightingDiagram(f.type) : '')}
                    
                    ${detailed.purpose ? `
                        <div class="feature-meaning">
                            <strong>光线效果：</strong>${detailed.purpose}
                        </div>
                    ` : (typeof getLightingMeaning === 'function' ? `
                        <div class="feature-meaning">
                            ${getLightingMeaning(f.type) || ''}
                        </div>
                    ` : '')}
                    
                    ${detailed.parameters && Object.keys(detailed.parameters).length > 0 ? `
                        <div class="feature-params">
                            <div class="params-label">光源配置：</div>
                            ${Object.entries(detailed.parameters).map(([key, val]) => `
                                <div class="param-item">
                                    <span class="param-key">${key}:</span>
                                    <span class="param-value">${val}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function renderColorAnalysis(features) {
    console.log('renderColorAnalysis 调用，特征数量:', features.length);
    
    if (features.length === 0) {
        return '<div class="detail-section"><h4 class="section-title">🎨 调色分析</h4><p>无调色特征</p></div>';
    }
    
    let html = '<div class="detail-section"><h4 class="section-title">🎨 调色分析</h4>';
    
    features.forEach(f => {
        const detailed = f.detailed_description || {};
        
        html += `
            <div class="feature-card">
                <div class="feature-header">
                    <span class="feature-badge">${f.value}</span>
                    <span class="confidence-badge">${(f.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="feature-body">
                    ${detailed.summary ? `
                        <div class="feature-summary">${detailed.summary}</div>
                    ` : ''}
                    
                    ${detailed.technical_terms && detailed.technical_terms.length > 0 ? `
                        <div class="feature-terms">
                            <div class="terms-label">专业术语：</div>
                            <div class="terms-list">
                                ${detailed.technical_terms.map(term => `<span class="term-badge">${term}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${detailed.purpose ? `
                        <div class="feature-meaning">
                            <strong>整体氛围：</strong>${detailed.purpose}
                        </div>
                    ` : (typeof getColorMeaning === 'function' ? `
                        <div class="feature-meaning">
                            ${getColorMeaning(f.type) || ''}
                        </div>
                    ` : '')}
                    
                    ${detailed.parameters && Object.keys(detailed.parameters).length > 0 ? `
                        <div class="feature-params color-params">
                            <div class="params-label">调色参数：</div>
                            ${Object.entries(detailed.parameters).map(([key, val]) => `
                                <div class="param-item">
                                    <span class="param-key">${key}:</span>
                                    <span class="param-value">${val}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : (typeof getColorParameters === 'function' ? getColorParameters(f.type) : '')}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function renderFeatureDetail(feature) {
    return `
        <div class="feature-card">
            <div class="feature-header">
                <span class="feature-badge">${feature.type}</span>
                <span class="confidence-badge">${(feature.confidence * 100).toFixed(0)}%</span>
            </div>
            <div class="feature-body">
                <div class="feature-value">${feature.value}</div>
                <div class="feature-meaning">
                    ${getFeatureMeaning(feature.category, feature.type)}
                </div>
            </div>
        </div>
    `;
}

function getFeatureMeaning(category, type) {
    if (category === 'camera_motion') {
        return getShotMeaning(type) || getMovementMeaning(type) || getAngleMeaning(type);
    } else if (category === 'lighting') {
        return getLightingMeaning(type);
    } else if (category === 'color_grading') {
        return getColorMeaning(type);
    }
    return '';
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
        
        // 更新播放头位置
        if (playhead && !isNaN(progress)) {
            updatePlayheadPosition(progress);
            console.log('更新播放头:', progress.toFixed(2) + '%');
        }
    });
    
    // 视频加载完成
    video.addEventListener('loadedmetadata', () => {
        const duration = video.duration * 1000;
        timeTotal.textContent = formatTime(duration);
        state.duration = duration;
        
        // 初始化播放头位置
        updatePlayheadPosition(0);
        console.log('视频加载完成，初始化播放头');
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

function updatePlayheadPosition(progress) {
    const playhead = document.getElementById('playhead');
    const tracksContainer = document.getElementById('tracks-container');
    
    if (!playhead || !tracksContainer) {
        console.log('播放头元素未找到', {playhead: !!playhead, container: !!tracksContainer});
        return;
    }
    
    // 获取轨道容器的宽度（减去padding和轨道标题宽度）
    const containerRect = tracksContainer.getBoundingClientRect();
    const trackHeaderWidth = 120; // 轨道标题宽度
    const padding = 16; // padding
    const trackContentWidth = containerRect.width - trackHeaderWidth - padding * 2;
    
    // 计算播放头的位置（相对于轨道容器）
    // 基准位置是轨道标题宽度 + padding
    const baseLeft = trackHeaderWidth + padding;
    const offsetLeft = (trackContentWidth * progress / 100);
    const playheadLeft = baseLeft + offsetLeft;
    
    console.log('播放头位置:', {
        progress: progress.toFixed(2),
        trackContentWidth,
        playheadLeft: playheadLeft.toFixed(2)
    });
    
    playhead.style.left = `${playheadLeft}px`;
    playhead.style.display = 'block';
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

// ========== 时间标尺点击跳转 ==========
function setupTimelineRulerClick() {
    const timelineRuler = document.getElementById('timeline-ruler');
    const tracksContainer = document.getElementById('tracks-container');
    const video = document.getElementById('preview-video');
    
    if (!timelineRuler) return;
    
    // 给时间标尺和轨道容器都添加点击事件
    [timelineRuler, tracksContainer].forEach(element => {
        if (!element) return;
        
        element.addEventListener('click', (e) => {
            if (!video || !video.duration) return;
            
            // 如果点击的是轨道标题区域，忽略
            if (e.target.closest('.track-header')) return;
            
            // 如果点击的是片段（segment），忽略（让片段自己的事件处理）
            if (e.target.closest('.segment')) return;
            
            // 计算点击位置对应的时间
            const rect = element.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            
            // 减去左侧轨道标题宽度和padding
            const trackHeaderWidth = 120;
            const padding = 16;
            const adjustedClickX = clickX - trackHeaderWidth - padding;
            const trackContentWidth = rect.width - trackHeaderWidth - padding * 2;
            
            if (adjustedClickX < 0) return; // 点击在标题区域
            
            const progress = Math.max(0, Math.min(1, adjustedClickX / trackContentWidth));
            const targetTime = progress * video.duration;
            
            // 跳转到指定时间
            video.currentTime = Math.max(0, Math.min(targetTime, video.duration));
            
            // 立即更新播放头位置
            updatePlayheadPosition(progress * 100);
        });
    });
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

// ========== 历史记录 ==========
async function showHistoryView() {
    // 隐藏Learn界面（但不清空，保持后台任务继续）
    document.querySelector('.sidebar').style.display = 'none';
    const mainContent = document.querySelector('.main-content');
    
    // 显示加载状态
    mainContent.innerHTML = `
        <div class="history-container">
            <div class="history-header">
                <h2 class="history-title">📚 分析历史</h2>
                <div style="display: flex; gap: 8px;">
                    ${state.currentJobId ? '<button class="btn-secondary" onclick="backToCurrentJob()">⬅️ 返回当前任务</button>' : ''}
                    <button class="btn-secondary" onclick="refreshHistory()">🔄 刷新</button>
                </div>
            </div>
            <div class="loading-state" style="display: flex;">
                <div class="loading-spinner"></div>
                <div class="loading-title">加载历史记录...</div>
            </div>
        </div>
    `;
    
    // 加载历史记录
    await loadHistory();
}

// 返回当前正在进行的任务
function backToCurrentJob() {
    if (!state.currentJobId) {
        alert('没有正在进行的任务');
        return;
    }
    
    // 切换回 learn 模式
    elements.navTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === 'learn');
    });
    state.mode = 'learn';
    
    // 显示 learn 界面
    document.querySelector('.sidebar').style.display = 'block';
    
    // 重新加载当前任务
    loadHistoryJob(state.currentJobId);
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/video-analysis/history?limit=50`);
        if (!response.ok) throw new Error('加载历史记录失败');
        
        const history = await response.json();
        state.historyList = history;
        
        renderHistory(history);
    } catch (error) {
        console.error('加载历史记录失败:', error);
        const mainContent = document.querySelector('.main-content');
        mainContent.innerHTML = `
            <div class="history-container">
                <div class="history-header">
                    <h2 class="history-title">📚 分析历史</h2>
                    <button class="btn-secondary" onclick="refreshHistory()">🔄 刷新</button>
                </div>
                <div class="empty-state" style="display: flex;">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-title">加载失败</div>
                    <div class="empty-text">${error.message}</div>
                </div>
            </div>
        `;
    }
}

function renderHistory(history) {
    const mainContent = document.querySelector('.main-content');
    
    if (history.length === 0) {
        mainContent.innerHTML = `
            <div class="history-container">
                <div class="history-header">
                    <h2 class="history-title">📚 分析历史</h2>
                    <button class="btn-secondary" onclick="refreshHistory()">🔄 刷新</button>
                </div>
                <div class="empty-state" style="display: flex;">
                    <div class="empty-icon">📝</div>
                    <div class="empty-title">暂无历史记录</div>
                    <div class="empty-text">开始分析你的第一个视频吧</div>
                </div>
            </div>
        `;
        return;
    }
    
    const historyHTML = history.map(item => {
        const statusBadge = {
            'succeeded': '<span class="status-badge status-success">✓ 完成</span>',
            'failed': '<span class="status-badge status-error">✗ 失败</span>',
            'running': '<span class="status-badge status-running">⟳ 进行中</span>',
            'queued': '<span class="status-badge status-queued">⋯ 排队中</span>'
        }[item.status] || '<span class="status-badge">未知</span>';
        
        const learningPointsHTML = item.learning_points && item.learning_points.length > 0
            ? item.learning_points.map(point => `<li class="learning-point">• ${point}</li>`).join('')
            : '<li class="learning-point">暂无学习要点</li>';
        
        const thumbnailStyle = item.thumbnail_url 
            ? `background-image: url('${item.thumbnail_url}');`
            : 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);';
        
        return `
            <div class="history-item">
                <button class="btn-delete-history" onclick="deleteHistoryJob(event, '${item.job_id}')" title="删除此记录">
                    <span class="delete-icon">🗑️</span>
                </button>
                <div class="history-clickable" onclick="loadHistoryJob('${item.job_id}')">
                    <div class="history-thumbnail" style="${thumbnailStyle}">
                        ${!item.thumbnail_url ? '<div class="thumbnail-placeholder">🎬</div>' : ''}
                    </div>
                    <div class="history-content">
                        <div class="history-item-header">
                            <h3 class="history-item-title">${item.title || '未命名任务'}</h3>
                            ${statusBadge}
                        </div>
                        <div class="history-meta">
                            <span class="meta-item">📹 ${item.segment_count || 0} 个镜头</span>
                            <span class="meta-item">⏱️ ${item.duration_sec ? (item.duration_sec).toFixed(1) + 's' : '未知'}</span>
                            <span class="meta-item">📅 ${formatDate(item.created_at)}</span>
                        </div>
                        <div class="learning-points-preview">
                            <div class="learning-title">💡 学习要点：</div>
                            <ul class="learning-list">
                                ${learningPointsHTML}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    mainContent.innerHTML = `
        <div class="history-container">
            <div class="history-header">
                <h2 class="history-title">📚 分析历史</h2>
                <button class="btn-secondary" onclick="refreshHistory()">🔄 刷新</button>
            </div>
            <div class="history-list">
                ${historyHTML}
            </div>
        </div>
    `;
}

async function loadHistoryJob(jobId) {
    console.log('loadHistoryJob 被调用, jobId:', jobId);
    
    // 切换回Learn模式并加载该Job
    state.mode = 'learn';
    state.currentJobId = jobId;
    
    // 更新导航
    elements.navTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.mode === 'learn');
    });
    
    // 显示Learn界面
    document.querySelector('.sidebar').style.display = 'block';
    
    // 使用 restoreLearnView 来恢复界面
    restoreLearnView();
    
    // 加载Job数据
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`);
        if (!response.ok) throw new Error('加载任务失败');
        
        const data = await response.json();
        console.log('历史任务数据:', data);
        
        if (data.status === 'succeeded' && data.result) {
            state.analysisResult = data.result;
            
            // 从服务器获取视频路径
            // 假设视频存储在 data/jobs/{jobId}/target/input_video.mp4
            const videoPath = `/data/jobs/${jobId}/target/input_video.mp4`;
            
            // 加载视频
            const video = document.getElementById('preview-video');
            if (video) {
                video.src = videoPath;
                video.load();
                console.log('视频路径已设置:', videoPath);
            }
            
            // 显示时间轴
            showTimeline(data.result, false);
            console.log('时间轴已显示');
            
        } else if (data.status === 'running') {
            // 如果任务还在运行中
            elements.loadingState.style.display = 'flex';
            elements.loadingProgress.textContent = `任务进行中：${data.progress?.message || '处理中...'}`;
            alert('该任务还在进行中，请稍后查看');
        } else if (data.status === 'failed') {
            throw new Error(data.error?.message || '任务失败');
        } else {
            throw new Error('任务未完成');
        }
    } catch (error) {
        console.error('加载历史任务失败:', error);
        alert('加载失败: ' + error.message);
        showEmpty();
    }
}

async function refreshHistory() {
    await loadHistory();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

// ========== 删除历史记录 ==========
async function deleteHistoryJob(event, jobId) {
    // 阻止事件冒泡，避免触发卡片点击
    event.stopPropagation();
    
    // 确认删除
    const confirmed = confirm('确定要删除这条历史记录吗？\n\n删除后将无法恢复，包括：\n• 分析结果\n• 视频文件\n• 关键帧图片');
    
    if (!confirmed) {
        return;
    }
    
    try {
        // 显示加载提示
        const button = event.currentTarget;
        const originalHTML = button.innerHTML;
        button.innerHTML = '<span class="delete-icon">⏳</span>';
        button.disabled = true;
        
        // 调用删除 API
        const response = await fetch(`${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('删除失败');
        }
        
        const result = await response.json();
        console.log('删除成功:', result);
        
        // 从列表中移除
        state.historyList = state.historyList.filter(item => item.job_id !== jobId);
        
        // 如果删除的是当前任务，清空状态
        if (state.currentJobId === jobId) {
            state.currentJobId = null;
            state.analysisResult = null;
        }
        
        // 刷新历史记录列表
        await loadHistory();
        
        // 显示成功提示
        alert('✓ 删除成功');
        
    } catch (error) {
        console.error('删除历史记录失败:', error);
        alert('删除失败: ' + error.message);
        
        // 恢复按钮
        const button = event.currentTarget;
        button.innerHTML = '<span class="delete-icon">🗑️</span>';
        button.disabled = false;
    }
}

// ========== 启动 ==========
console.log('App.js 加载完成');
console.log('feature-meanings.js 函数检查:', {
    getShotMeaning: typeof getShotMeaning,
    getMovementMeaning: typeof getMovementMeaning,
    getAngleMeaning: typeof getAngleMeaning,
    getLightingMeaning: typeof getLightingMeaning,
    getColorMeaning: typeof getColorMeaning
});

init();

