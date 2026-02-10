import React, { useState, useRef } from 'react';
import { 
  CloudArrowUpIcon, 
  SpeakerWaveIcon, 
  DocumentTextIcon, 
  ArrowDownTrayIcon, 
  PlayIcon, 
  BookOpenIcon, 
  SparklesIcon,
  MicrophoneIcon,
  HandRaisedIcon,
  HomeIcon,
  Bars3Icon,
  XMarkIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

function App() {
  // Navigation state
  const [currentPage, setCurrentPage] = useState('text-to-audio');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Text-to-Audio state
  const [status, setStatus] = useState("idle"); 
  const [audioUrl, setAudioUrl] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const audioRef = useRef(null);
  
  // Upload history
  const [uploadHistory, setUploadHistory] = useState([]);

  const handleFileUpload = async (file) => {
    if (!file || file.type !== "application/pdf") {
      alert("Please upload a valid PDF file.");
      return;
    }
    setStatus("uploading");
    setErrorMessage("");
    setAudioUrl(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      setStatus("processing"); 
      const response = await fetch('http://localhost:8000/api/process-notes', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error("Processing failed.");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setStatus("success");
      
      // Create PDF URL for viewing
      const pdfUrl = URL.createObjectURL(file);
      
      // Add to history
      const newEntry = {
        id: Date.now(),
        fileName: file.name,
        uploadDate: new Date().toLocaleString(),
        audioUrl: url,
        pdfUrl: pdfUrl,
        size: (file.size / 1024).toFixed(2) + ' KB'
      };
      setUploadHistory(prev => [newEntry, ...prev]);
      
      setTimeout(() => {
        if (audioRef.current) audioRef.current.play().catch(e => console.log(e));
      }, 500);

    } catch (error) {
      console.error(error);
      setStatus("error");
      setErrorMessage(error.message);
    }
  };

  const deleteHistoryItem = (id) => {
    setUploadHistory(prev => prev.filter(item => item.id !== id));
  };

  const navItems = [
    { id: 'text-to-audio', label: 'Text to Audio', icon: SpeakerWaveIcon, description: 'Convert PDFs to audio' },
    { id: 'audio-to-text', label: 'Audio to Text', icon: MicrophoneIcon, description: 'Transcribe audio files' },
    { id: 'sign-language', label: 'Sign Language', icon: HandRaisedIcon, description: 'Sign language interpreter' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-700"></div>
      </div>

      {/* Layout Container */}
      <div className="relative z-10 flex min-h-screen">
        
        {/* SIDEBAR */}
        <aside 
          className={`${sidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-white/10 backdrop-blur-xl border-r border-white/20 flex-shrink-0 overflow-hidden`}
          aria-label="Main navigation"
        >
          <div className="p-6 h-full flex flex-col">
            {/* Logo */}
            <div className="mb-8">
              <h2 className="text-2xl font-black text-white flex items-center gap-2">
                <SparklesIcon className="w-7 h-7 text-purple-300" />
                AudioScholar
              </h2>
              <p className="text-xs text-slate-400 mt-1">Accessibility Suite</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1" role="navigation">
              <ul className="space-y-2">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentPage === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        onClick={() => setCurrentPage(item.id)}
                        className={`w-full text-left p-4 rounded-xl transition-all group ${
                          isActive 
                            ? 'bg-white/20 text-white shadow-lg' 
                            : 'text-slate-300 hover:bg-white/10 hover:text-white'
                        }`}
                        aria-label={`Navigate to ${item.label}`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className={`w-6 h-6 ${isActive ? 'text-purple-300' : 'text-slate-400 group-hover:text-purple-300'}`} />
                          <div className="flex-1">
                            <div className="font-semibold">{item.label}</div>
                            <div className="text-xs opacity-70">{item.description}</div>
                          </div>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </nav>

            {/* Footer info */}
            <div className="mt-auto pt-6 border-t border-white/10">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>Fully Accessible</span>
              </div>
              <p className="text-xs text-slate-500 mt-2">Screen reader optimized</p>
            </div>
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="flex-1 overflow-auto" role="main">
          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="fixed top-6 left-6 z-50 lg:hidden bg-white/10 backdrop-blur-xl p-3 rounded-xl border border-white/20 text-white hover:bg-white/20 transition-all"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            {sidebarOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
          </button>

          <div className="p-6 lg:p-12">
            
            {/* TEXT TO AUDIO PAGE */}
            {currentPage === 'text-to-audio' && (
              <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12 space-y-4">
                  <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20 mb-4">
                    <SpeakerWaveIcon className="w-4 h-4 text-purple-300" />
                    <span className="text-sm text-purple-200 font-medium">Text to Audio Converter</span>
                  </div>
                  
                  <h1 className="text-5xl lg:text-6xl font-black tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-white via-purple-200 to-white">
                    PDF to Podcast
                  </h1>
                  <p className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
                    Upload your lecture notes and we'll convert them to high-quality audio. Study on-the-go!
                  </p>
                </div>

                {/* Upload Card */}
                <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-white/20 mb-8">
                  
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl">
                      <BookOpenIcon className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-purple-900">PDF</div>
                      <div className="text-xs text-purple-600">Any Format</div>
                    </div>
                    <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl">
                      <SpeakerWaveIcon className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-blue-900">Audio</div>
                      <div className="text-xs text-blue-600">High Quality</div>
                    </div>
                    <div className="text-center p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl">
                      <SparklesIcon className="w-6 h-6 text-indigo-600 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-indigo-900">AI</div>
                      <div className="text-xs text-indigo-600">Smart OCR</div>
                    </div>
                  </div>

                  {/* Upload Zone */}
                  <div 
                    className={`relative border-3 border-dashed rounded-2xl h-72 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 group overflow-hidden
                      ${status === "processing" ? "border-purple-400 bg-gradient-to-br from-purple-50 to-blue-50 scale-[1.02]" : 
                        status === "error" ? "border-red-400 bg-red-50 shake" :
                        status === "success" ? "border-green-400 bg-gradient-to-br from-green-50 to-emerald-50" :
                        "border-slate-300 hover:border-purple-400 hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 hover:scale-[1.02] hover:shadow-lg"}`}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      handleFileUpload(e.dataTransfer.files[0]);
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label="File upload zone. Click or drag and drop a PDF file here"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-purple-400/0 via-purple-400/10 to-purple-400/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                    
                    <label className="cursor-pointer w-full h-full flex flex-col items-center justify-center z-10 p-8 relative">
                      
                      {status === "idle" && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                          <div className="relative">
                            <CloudArrowUpIcon className="h-24 w-24 text-purple-400 mx-auto group-hover:text-purple-600 transition-all group-hover:scale-110" />
                            <div className="absolute inset-0 bg-purple-400/20 blur-2xl rounded-full group-hover:bg-purple-400/30 transition-all"></div>
                          </div>
                          <div>
                            <span className="text-2xl font-bold text-slate-700 group-hover:text-purple-700 block transition-colors">
                              Drop your PDF here
                            </span>
                            <span className="text-sm text-slate-500 mt-2 block">or click to browse files</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-100 px-4 py-2 rounded-full">
                            <SparklesIcon className="w-3 h-3" />
                            Supports scanned & digital PDFs
                          </div>
                        </div>
                      )}

                      {status === "uploading" && (
                        <div className="animate-in fade-in zoom-in duration-300">
                          <DocumentTextIcon className="h-20 w-20 text-purple-500 mb-4 animate-bounce" />
                          <span className="text-lg text-purple-700 font-semibold">Uploading...</span>
                        </div>
                      )}
                      
                      {status === "processing" && (
                        <div className="flex flex-col items-center gap-6 animate-in fade-in zoom-in duration-500">
                          <div className="relative">
                            <div className="w-16 h-16 border-4 border-purple-200 rounded-full"></div>
                            <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin absolute inset-0"></div>
                            <SparklesIcon className="w-6 h-6 text-purple-600 absolute inset-0 m-auto animate-pulse" />
                          </div>
                          <div className="text-center">
                            <span className="text-xl text-purple-900 font-bold block mb-1">AI is working its magic</span>
                            <span className="text-sm text-purple-600">Reading, processing, and converting to audio...</span>
                          </div>
                        </div>
                      )}
                      
                      {status === "success" && (
                        <div className="animate-in fade-in zoom-in duration-500">
                          <div className="relative mb-4">
                            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                              <SpeakerWaveIcon className="h-10 w-10 text-green-600 animate-pulse" />
                            </div>
                            <div className="absolute -top-2 -right-2 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-xl">✓</span>
                            </div>
                          </div>
                          <span className="text-xl text-green-900 font-bold">Audio Ready!</span>
                        </div>
                      )}
                      
                      <input 
                        type="file" 
                        className="hidden" 
                        accept=".pdf" 
                        onChange={(e) => handleFileUpload(e.target.files[0])}
                        disabled={status === "processing"}
                        aria-label="Upload PDF file for audio conversion"
                      />
                    </label>
                  </div>

                  {/* Audio Player */}
                  {status === "success" && audioUrl && (
                    <div className="mt-8 bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 rounded-2xl p-8 border-2 border-green-200 animate-in fade-in slide-in-from-bottom-6 duration-700 shadow-lg">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                          <PlayIcon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <h3 className="text-green-900 font-bold text-xl">Your Audio is Ready</h3>
                          <p className="text-green-700 text-sm">Listen or download to study on-the-go</p>
                        </div>
                      </div>
                      
                      <audio 
                        ref={audioRef} 
                        controls 
                        src={audioUrl} 
                        className="w-full mb-5 rounded-lg shadow-md accent-green-600"
                        aria-label="Audio player for converted lecture notes"
                      />
                      
                      <a 
                        href={audioUrl} 
                        download="lecture_audio.mp3"
                        className="flex items-center justify-center gap-3 w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-4 px-6 rounded-xl shadow-xl hover:shadow-2xl transition-all active:scale-95 group"
                        aria-label="Download audio file as MP3"
                      >
                        <ArrowDownTrayIcon className="h-5 w-5 group-hover:animate-bounce" />
                        Download MP3
                      </a>
                    </div>
                  )}

                  {/* Error */}
                  {status === "error" && (
                    <div className="mt-6 p-5 bg-gradient-to-r from-red-50 to-pink-50 text-red-700 rounded-xl font-medium border-2 border-red-200 flex items-center gap-3 animate-in fade-in shake duration-500 shadow-lg" role="alert">
                      <div className="w-10 h-10 bg-red-200 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-xl" aria-hidden="true">⚠️</span>
                      </div>
                      <div>
                        <div className="font-bold text-red-900">Oops! Something went wrong</div>
                        <div className="text-sm text-red-600">{errorMessage || "Please try again with a different file"}</div>
                      </div>
                    </div>
                  )}
                </div>

                {/* PDF VIEWER WITH AUDIO */}
                {uploadHistory.length > 0 && (
                  <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/20">
                    <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                      <DocumentTextIcon className="w-6 h-6 text-purple-600" />
                      Your Documents
                    </h2>
                    
                    <div className="space-y-6">
                      {uploadHistory.map((item) => (
                        <div key={item.id} className="border-2 border-slate-200 rounded-2xl overflow-hidden hover:border-purple-300 transition-all">
                          {/* Header */}
                          <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                                <DocumentTextIcon className="w-6 h-6 text-white" />
                              </div>
                              <div>
                                <h3 className="font-bold text-slate-800">{item.fileName}</h3>
                                <p className="text-xs text-slate-600">{item.uploadDate} • {item.size}</p>
                              </div>
                            </div>
                            <button
                              onClick={() => deleteHistoryItem(item.id)}
                              className="p-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
                              aria-label={`Delete ${item.fileName}`}
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </div>

                          {/* Content Grid */}
                          <div className="grid lg:grid-cols-2 gap-6 p-6">
                            {/* PDF Viewer */}
                            <div className="space-y-3">
                              <h4 className="font-semibold text-slate-700 flex items-center gap-2">
                                <BookOpenIcon className="w-5 h-5 text-purple-600" />
                                Document Preview
                              </h4>
                              <div className="bg-slate-100 rounded-xl overflow-hidden border-2 border-slate-200" style={{ height: '500px' }}>
                                <iframe
                                  src={item.pdfUrl}
                                  className="w-full h-full"
                                  title={`PDF viewer for ${item.fileName}`}
                                  aria-label={`PDF preview of ${item.fileName}`}
                                />
                              </div>
                              <a
                                href={item.pdfUrl}
                                download={item.fileName}
                                className="flex items-center justify-center gap-2 w-full bg-purple-100 hover:bg-purple-200 text-purple-700 font-semibold py-3 px-4 rounded-xl transition-all"
                                aria-label={`Download PDF ${item.fileName}`}
                              >
                                <ArrowDownTrayIcon className="w-5 h-5" />
                                Download PDF
                              </a>
                            </div>

                            {/* Audio Player */}
                            <div className="space-y-3">
                              <h4 className="font-semibold text-slate-700 flex items-center gap-2">
                                <SpeakerWaveIcon className="w-5 h-5 text-green-600" />
                                Audio Version
                              </h4>
                              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border-2 border-green-200" style={{ height: '500px' }}>
                                <div className="h-full flex flex-col justify-center">
                                  {/* Waveform Visualization */}
                                  <div className="mb-8 flex items-center justify-center gap-1 h-32">
                                    {[...Array(40)].map((_, i) => (
                                      <div
                                        key={i}
                                        className="w-1 bg-green-400 rounded-full animate-pulse"
                                        style={{
                                          height: `${Math.random() * 100 + 20}%`,
                                          animationDelay: `${i * 0.05}s`
                                        }}
                                      />
                                    ))}
                                  </div>

                                  {/* Audio Controls */}
                                  <div className="space-y-4">
                                    <audio 
                                      controls 
                                      src={item.audioUrl} 
                                      className="w-full accent-green-600"
                                      aria-label={`Audio player for ${item.fileName}`}
                                    />
                                    
                                    <div className="grid grid-cols-2 gap-3 text-sm">
                                      <div className="bg-white/60 rounded-lg p-3 text-center">
                                        <div className="text-xs text-slate-600">Duration</div>
                                        <div className="font-bold text-slate-800">--:--</div>
                                      </div>
                                      <div className="bg-white/60 rounded-lg p-3 text-center">
                                        <div className="text-xs text-slate-600">Format</div>
                                        <div className="font-bold text-slate-800">MP3</div>
                                      </div>
                                    </div>

                                    <a
                                      href={item.audioUrl}
                                      download={item.fileName.replace('.pdf', '.mp3')}
                                      className="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg hover:shadow-xl active:scale-95"
                                      aria-label={`Download audio for ${item.fileName}`}
                                    >
                                      <ArrowDownTrayIcon className="w-5 h-5" />
                                      Download Audio
                                    </a>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AUDIO TO TEXT PAGE */}
            {currentPage === 'audio-to-text' && (
              <div className="max-w-4xl mx-auto">
                <div className="text-center mb-12">
                  <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20 mb-4">
                    <MicrophoneIcon className="w-4 h-4 text-blue-300" />
                    <span className="text-sm text-blue-200 font-medium">Audio to Text Transcription</span>
                  </div>
                  <h1 className="text-5xl lg:text-6xl font-black tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-200 to-white">
                    Audio Transcription
                  </h1>
                  <p className="text-lg text-slate-300">
                    Upload audio files and get accurate text transcriptions
                  </p>
                </div>

                <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-white/20">
                  <div className="text-center py-20">
                    <MicrophoneIcon className="w-24 h-24 text-blue-400 mx-auto mb-6" />
                    <h3 className="text-2xl font-bold text-slate-700 mb-2">Coming Soon</h3>
                    <p className="text-slate-500">Audio transcription feature is under development</p>
                  </div>
                </div>
              </div>
            )}

            {/* SIGN LANGUAGE PAGE */}
            {currentPage === 'sign-language' && (
              <div className="max-w-4xl mx-auto">
                <div className="text-center mb-12">
                  <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20 mb-4">
                    <HandRaisedIcon className="w-4 h-4 text-orange-300" />
                    <span className="text-sm text-orange-200 font-medium">Sign Language Interpreter</span>
                  </div>
                  <h1 className="text-5xl lg:text-6xl font-black tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-white via-orange-200 to-white">
                    Sign Language
                  </h1>
                  <p className="text-lg text-slate-300">
                    Real-time sign language interpretation powered by AI
                  </p>
                </div>

                <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-white/20">
                  <div className="text-center py-20">
                    <HandRaisedIcon className="w-24 h-24 text-orange-400 mx-auto mb-6" />
                    <h3 className="text-2xl font-bold text-slate-700 mb-2">Coming Soon</h3>
                    <p className="text-slate-500">Sign language interpreter feature is under development</p>
                  </div>
                </div>
              </div>
            )}

          </div>
        </main>
      </div>

      <style jsx>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        .shake {
          animation: shake 0.5s ease-in-out;
        }
        .delay-700 {
          animation-delay: 0.7s;
        }
      `}</style>
    </div>
  );
}

export default App;