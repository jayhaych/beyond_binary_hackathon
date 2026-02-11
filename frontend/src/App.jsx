import React, { useState, useRef, useEffect } from 'react';
import { 
  CloudArrowUpIcon, 
  SpeakerWaveIcon, 
  DocumentTextIcon, 
  ArrowDownTrayIcon, 
  PlayIcon, 
  SparklesIcon,
  MicrophoneIcon,
  HandRaisedIcon,
  Bars3Icon,
  XMarkIcon,
  TrashIcon,
  AcademicCapIcon, 
  EyeSlashIcon,
  CheckCircleIcon,
  ArrowRightIcon, 
  HomeIcon        
} from '@heroicons/react/24/outline';

function App() {
  // --- STATE MANAGEMENT ---
  const [showLanding, setShowLanding] = useState(true);
  const [currentPage, setCurrentPage] = useState('text-to-audio');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Text-to-Audio State
  const [status, setStatus] = useState("idle"); 
  const [audioUrl, setAudioUrl] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [duplicateFileName, setDuplicateFileName] = useState("");
  const audioRef = useRef(null);
  
  // Visual Quiz State
  const [quizStatus, setQuizStatus] = useState("idle"); 
  const [quizData, setQuizData] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);

  // Blind Mode State
  const [blindModeStatus, setBlindModeStatus] = useState("idle");
  const [blindQuizResults, setBlindQuizResults] = useState(null);

  // History State
  const [uploadHistory, setUploadHistory] = useState([]);

  // Transcript State
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptText, setTranscriptText] = useState("");
  const [transcriptStatus, setTranscriptStatus] = useState("idle");
  const [recordingTime, setRecordingTime] = useState(0);
  const [lastRecordingUrl, setLastRecordingUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingIntervalRef = useRef(null);
  const recordingStreamRef = useRef(null);

  // --- [FIXED] HELPER FUNCTION ---
  // We added a timeout to ensure the browser audio engine doesn't get stuck
  const speakUI = (text) => {
    if ('speechSynthesis' in window) {
      // 1. Stop whatever is currently talking
      window.speechSynthesis.cancel(); 

      const utterance = new SpeechSynthesisUtterance(text);
      
      // 2. Small delay to ensure the 'cancel' finished processing before we speak again
      setTimeout(() => {
        window.speechSynthesis.speak(utterance);
      }, 50);
    }
  };

  // --- WELCOME MESSAGE EFFECT ---
  // This runs every time 'showLanding' changes to true
  useEffect(() => {
    if (showLanding) {
      // Delay slightly so the page appears before the voice starts
      const timer = setTimeout(() => {
        speakUI(
          "Hi there! Want to learn with sound and voice guidance? Double-tap anywhere to jump to Audio mode. Happy exploring visually? Just keep going to the Visual Learning section."
        );
      }, 800);

      // Cleanup: Stop speaking if the user leaves the page quickly
      return () => {
        clearTimeout(timer);
        window.speechSynthesis.cancel(); 
      };
    }
  }, [showLanding]);

  // --- HANDLERS ---

  const enterVisualMode = () => {
    setShowLanding(false);
    setCurrentPage('text-to-audio'); 
  };

  const enterAudioMode = () => {
    setShowLanding(false);
    setCurrentPage('blind-mode'); 
    speakUI("Welcome to Audio Mode. You are now on the Blind Mode Quiz page.");
  };

  const goHome = () => {
    setShowLanding(true);
    setBlindModeStatus("idle");
    setBlindQuizResults(null);
    // Note: The useEffect above will trigger automatically when showLanding becomes true
  };

  // File Upload Handler
  const handleFileUpload = async (file) => {
    if (!file || file.type !== "application/pdf") {
      alert("Please upload a valid PDF file.");
      return;
    }

    const isDuplicate = uploadHistory.some(item => item.fileName === file.name);
    if (isDuplicate) {
      setStatus("duplicate");
      setDuplicateFileName(file.name);
      setTimeout(() => {
        setStatus("idle");
        setDuplicateFileName("");
      }, 5000);
      return;
    }

    setStatus("uploading");
    setErrorMessage("");
    setAudioUrl(null);
    setQuizData(null); 
    setShowQuiz(false);

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
      
      const pdfUrl = URL.createObjectURL(file);
      
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

      setTimeout(() => setStatus("idle"), 3000);

    } catch (error) {
      console.error(error);
      setStatus("error");
      setErrorMessage(error.message);
    }
  };

  const handleGenerateQuiz = async () => {
    setQuizStatus("loading");
    try {
      const res = await fetch('http://localhost:8000/api/generate-quiz');
      if (!res.ok) throw new Error("Failed to generate quiz");
      
      const data = await res.json();
      setQuizData(data);
      setQuizStatus("success");
      setShowQuiz(true);
    } catch (e) {
      console.error(e);
      setQuizStatus("error");
      alert("Could not generate quiz. Make sure you uploaded a PDF first!");
    }
  };

  const handleStartBlindMode = async () => {
    setBlindModeStatus("running");
    setBlindQuizResults(null); 
    
    speakUI("Starting Voice Quiz. Please listen to your speakers.");

    try {
      const res = await fetch('http://localhost:8000/api/start-blind-quiz', {
        method: 'POST'
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start");
      }

      const data = await res.json();
      setBlindQuizResults(data);
      setBlindModeStatus("success");
      speakUI("Quiz finished. Your results are on the screen.");

    } catch (e) {
      console.error(e);
      setBlindModeStatus("error");
      speakUI("An error occurred. Please check your connection.");
    }
  };

  const deleteHistoryItem = (id) => {
    setUploadHistory(prev => prev.filter(item => item.id !== id));
  };

  // --- TRANSCRIPT HANDLERS ---
  const startRecording = async () => {
    try {
      console.log("🎤 Starting recording...");
      setTranscriptStatus("recording");
      setRecordingTime(0);
      audioChunksRef.current = [];
      setTranscriptText("");
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordingStreamRef.current = stream;
      
      console.log("✅ Microphone access granted");
      
      // Create MediaRecorder with specific audio format
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.start();
      console.log("⏹️ Recording started");
      
      // Start recording timer
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      setIsRecording(true);
    } catch (error) {
      console.error("❌ Recording error:", error);
      setTranscriptStatus("error");
      setTranscriptText(`Microphone error: ${error.message}`);
    }
  };

  const stopRecording = async () => {
    if (!mediaRecorderRef.current) return;
    
    console.log("⏸️ Stopping recording...");
    setIsRecording(false);
    setTranscriptStatus("processing");
    clearInterval(recordingIntervalRef.current);
    
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;
      
      mediaRecorder.onstop = async () => {
        try {
          // Stop microphone stream
          recordingStreamRef.current?.getTracks().forEach(track => track.stop());
          console.log("✅ Recording stopped, processing audio...");
          
          // Create blob from audio chunks (webm format)
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          console.log(`📦 Created WebM blob: ${audioBlob.size} bytes`);
          
          // Create URL for playback
          const url = URL.createObjectURL(audioBlob);
          setLastRecordingUrl(url);
          
          // Convert webm to WAV format for vosk processing
          const arrayBuffer = await audioBlob.arrayBuffer();
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          
          try {
            console.log("🔄 Decoding audio using WebAudioAPI...");
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            console.log(`✅ Decoded: ${audioBuffer.numberOfChannels} ch, ${audioBuffer.sampleRate} Hz, ${audioBuffer.length} samples`);
            
            // Convert to WAV
            const wavBlob = audioBufferToWav(audioBuffer);
            console.log(`📦 Created WAV blob: ${wavBlob.size} bytes`);
            
            // Convert WAV blob to base64 using safe encoder
            const wavArrayBuffer = await wavBlob.arrayBuffer();
            const base64Audio = arrayBufferToBase64(wavArrayBuffer);
            
            console.log(`📤 Encoded to base64: ${base64Audio.length} chars`);
            
            // Send to backend
            console.log("📡 Sending to backend...");
            const response = await fetch('http://localhost:8000/api/transcribe-audio', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ audio_base64: base64Audio })
            });
            
            if (!response.ok) {
              const err = await response.json();
              throw new Error(err.detail || "Transcription failed");
            }
            
            const data = await response.json();
            console.log(`✅ Response: ${data.transcript}`);
            setTranscriptText(data.transcript);
            setTranscriptStatus("success");
            
            // Reset status after 3 seconds
            setTimeout(() => setTranscriptStatus("idle"), 3000);
          } catch (decodeError) {
            console.warn("⚠️ WebAudioAPI decode failed, attempting fallback:", decodeError);
            // Fallback: send raw webm for backend to handle
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64Audio = arrayBufferToBase64(uint8Array.buffer);
            
            console.log(`📤 Fallback: Sending ${base64Audio.length} chars of base64 webm audio`);
            
            const response = await fetch('http://localhost:8000/api/transcribe-audio', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ audio_base64: base64Audio })
            });
            
            if (!response.ok) {
              const err = await response.json();
              throw new Error(err.detail || "Transcription failed");
            }
            const data = await response.json();
            console.log(`✅ Fallback response: ${data.transcript}`);
            setTranscriptText(data.transcript);
            setTranscriptStatus("success");
          }
        } catch (error) {
          console.error("❌ Transcription error:", error);
          setTranscriptStatus("error");
          setTranscriptText(`Error: ${error.message}`);
        }
        
        resolve();
      };
      
      mediaRecorder.stop();
    });
  };

  // Helper function to convert AudioBuffer to WAV Blob
  const audioBufferToWav = (audioBuffer) => {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const frameLength = audioBuffer.length;
    const channelData = [];
    
    for (let i = 0; i < numberOfChannels; i++) {
      channelData.push(audioBuffer.getChannelData(i));
    }
    
    // Mix down to mono if needed
    let monoData;
    if (numberOfChannels > 1) {
      monoData = new Float32Array(frameLength);
      for (let i = 0; i < frameLength; i++) {
        let sum = 0;
        for (let channel = 0; channel < numberOfChannels; channel++) {
          sum += channelData[channel][i];
        }
        monoData[i] = sum / numberOfChannels;
      }
    } else {
      monoData = channelData[0];
    }
    
    // Encode to WAV
    const wavData = encodeWAV(monoData, sampleRate);
    return new Blob([wavData], { type: 'audio/wav' });
  };

  const encodeWAV = (samples, sampleRate) => {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    
    // Helper to write string
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    // WAV header
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true); // fmt chunk size
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, 1, true); // 1 channel (mono)
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); // byte rate
    view.setUint16(32, 2, true); // block align
    view.setUint16(34, 16, true); // bits per sample
    writeString(36, 'data');
    view.setUint32(40, samples.length * 2, true);
    
    // Write PCM samples
    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      offset += 2;
    }
    
    return buffer;
  };

  const copyTranscript = () => {
    navigator.clipboard.writeText(transcriptText);
    alert("Transcript copied to clipboard!");
  };

  // Safe base64 encoder for large binary data
  const arrayBufferToBase64 = (buffer) => {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    // Process in chunks to avoid "Maximum call stack size exceeded" error
    const chunkSize = 8192;
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      binary += String.fromCharCode.apply(null, chunk);
    }
    return btoa(binary);
  };

  const navItems = [
    { id: 'text-to-audio', label: 'Visual Learning', icon: SpeakerWaveIcon, description: 'Read & Listen' },
    { id: 'blind-mode', label: 'Audio Learning', icon: EyeSlashIcon, description: 'Voice-only Quiz' }, 
    { id: 'audio-to-text', label: 'Transcribe', icon: MicrophoneIcon, description: 'Audio to Text' },
    { id: 'sign-language', label: 'Sign Language', icon: HandRaisedIcon, description: 'Interpreter' },
  ];

  // =========================================================================
  // VIEW 1: LANDING PAGE (WELCOME SCREEN)
  // =========================================================================
  if (showLanding) {
    return (
      <div 
        // Double-Click Anywhere Handler
        onDoubleClick={enterAudioMode}
        className="min-h-screen bg-slate-900 relative overflow-hidden flex items-center justify-center p-6 cursor-pointer select-none"
        title="Double-click anywhere to start Audio Mode"
      >
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
           <div className="absolute top-0 left-0 w-full h-full bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
           <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/30 rounded-full blur-[100px] animate-pulse"></div>
           <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-600/30 rounded-full blur-[100px] animate-pulse delay-1000"></div>
        </div>

        <div className="relative z-10 max-w-6xl w-full">
           <div className="text-center mb-16 animate-in fade-in slide-in-from-bottom-10 duration-1000">
              
              {/* Main Title */}
              <h1 className="text-7xl md:text-8xl font-black text-white mb-6 tracking-tight">
                Omni<span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-emerald-400">Learn</span>
              </h1>
              <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
                An inclusive learning platform designed for everyone.
              </p>
              
              {/* Instructions Text */}
              <div className="mt-6 text-sm font-mono text-purple-200 bg-white/5 inline-block px-4 py-2 rounded-lg border border-white/10">
                 💡 Tip: Double-tap anywhere for Audio Mode
              </div>
           </div>

           <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* VISUAL CARD */}
              <button 
                onClick={(e) => { e.stopPropagation(); enterVisualMode(); }}
                className="group relative h-80 bg-gradient-to-br from-purple-900/50 to-slate-900/50 hover:from-purple-800/80 hover:to-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl p-8 text-left transition-all hover:-translate-y-2 hover:shadow-2xl hover:shadow-purple-500/20 flex flex-col justify-between overflow-hidden"
              >
                 <div className="absolute top-0 right-0 p-32 bg-purple-500/10 blur-3xl rounded-full group-hover:bg-purple-500/20 transition-all"></div>
                 
                 <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center border border-purple-500/30 mb-6 group-hover:scale-110 transition-transform">
                    <DocumentTextIcon className="w-8 h-8 text-purple-300" />
                 </div>
                 
                 <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Visual Learning</h2>
                    <p className="text-purple-200">Convert PDFs to Audio, read summaries, and take visual quizzes.</p>
                 </div>
                 
                 <div className="flex items-center gap-2 text-white font-bold mt-6 group-hover:gap-4 transition-all">
                    Enter Portal <ArrowRightIcon className="w-5 h-5" />
                 </div>
              </button>

              {/* AUDIO CARD */}
              <button 
                onClick={(e) => { e.stopPropagation(); enterAudioMode(); }}
                className="group relative h-80 bg-gradient-to-br from-emerald-900/50 to-slate-900/50 hover:from-emerald-800/80 hover:to-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl p-8 text-left transition-all hover:-translate-y-2 hover:shadow-2xl hover:shadow-emerald-500/20 flex flex-col justify-between overflow-hidden"
              >
                 <div className="absolute top-0 right-0 p-32 bg-emerald-500/10 blur-3xl rounded-full group-hover:bg-emerald-500/20 transition-all"></div>
                 
                 <div className="w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center border border-emerald-500/30 mb-6 group-hover:scale-110 transition-transform">
                    <EyeSlashIcon className="w-8 h-8 text-emerald-300" />
                 </div>
                 
                 <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Audio Learning</h2>
                    <p className="text-emerald-200">Fully accessible Blind Mode. Voice-controlled quizzes and navigation.</p>
                 </div>
                 
                 <div className="flex items-center gap-2 text-white font-bold mt-6 group-hover:gap-4 transition-all">
                    Enter Portal <ArrowRightIcon className="w-5 h-5" />
                 </div>
              </button>
           </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // VIEW 2: MAIN DASHBOARD
  // =========================================================================
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-200 via-blue-100 to-blue-200 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-400/10 rounded-full blur-3xl animate-pulse delay-700"></div>
      </div>

      <div className="relative z-10 flex min-h-screen">
        
        {/* SIDEBAR */}
        <aside 
          className={`${sidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-blue-950/85 backdrop-blur-xl border-r border-blue-500/40 flex-shrink-0 overflow-hidden flex flex-col`}
        >
          <div className="p-6 h-full flex flex-col">
            <div className="mb-8">
              <h2 className="text-2xl font-black text-white flex items-center gap-2">
                <SparklesIcon className="w-7 h-7 text-blue-400" />
                Omnilearn
              </h2>
              <p className="text-xs text-slate-400 mt-1">Accessibility Suite</p>
            </div>

            <nav className="flex-1">
              <ul className="space-y-2">
                {/* Home Button */}
                <li>
                  <button onClick={goHome} className="w-full text-left p-4 rounded-xl text-slate-300 hover:bg-blue-700/40 hover:text-white transition-all flex items-center gap-3">
                     <HomeIcon className="w-6 h-6 text-slate-400" />
                     <div className="font-semibold">Back to Home</div>
                  </button>
                </li>
                
                <div className="my-2 border-t border-blue-600/30"></div>

                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentPage === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        onClick={() => setCurrentPage(item.id)}
                        className={`w-full text-left p-4 rounded-xl transition-all group ${
                          isActive 
                            ? 'bg-blue-700/50 text-white shadow-lg' 
                            : 'text-slate-300 hover:bg-blue-700/40 hover:text-white'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className={`w-6 h-6 ${isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-cyan-400'}`} />
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
            
            <div className="mt-auto pt-6 border-t border-blue-600/30">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                <span>System Online</span>
              </div>
            </div>
          </div>
        </aside>

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 overflow-auto">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="fixed top-6 left-6 z-50 lg:hidden bg-blue-950/85 backdrop-blur-xl p-3 rounded-xl border border-blue-500/40 text-white hover:bg-blue-800/60 transition-all"
          >
            {sidebarOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
          </button>

          <div className="p-6 lg:p-12">
            
            {/* PAGE 1: TEXT TO AUDIO (Visual Learning) */}
            {currentPage === 'text-to-audio' && (
              <div className="max-w-5xl mx-auto animate-in fade-in zoom-in duration-500">
                <div className="text-center mb-12 space-y-4">
                  <div className="inline-flex items-center gap-2 bg-blue-400/20 backdrop-blur-sm px-4 py-2 rounded-full border border-blue-400/40 mb-4">
                    <SpeakerWaveIcon className="w-4 h-4 text-blue-700" />
                    <span className="text-sm text-blue-800 font-medium">Visual Learning Mode</span>
                  </div>
                  <h1 className="text-5xl lg:text-6xl font-black tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-blue-900 via-blue-700 to-blue-900">
                    PDF to Podcast
                  </h1>
                </div>

                <div className="grid lg:grid-cols-1 gap-8 mb-8">
                  <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-blue-300/40">
                    
                    {/* UPLOAD ZONE */}
                    <div 
                      className={`relative border-3 border-dashed rounded-2xl h-72 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 group overflow-hidden
                        ${status === "processing" ? "border-blue-500 bg-gradient-to-br from-blue-100 to-cyan-100 scale-[1.02]" : 
                          status === "error" ? "border-red-400 bg-red-50 shake" :
                          status === "duplicate" ? "border-yellow-400 bg-yellow-50 shake" :
                          status === "success" ? "border-green-400 bg-gradient-to-br from-green-50 to-emerald-50" :
                          "border-blue-400 hover:border-blue-600 hover:bg-gradient-to-br hover:from-blue-100 hover:to-cyan-100 hover:scale-[1.02] hover:shadow-lg"}`}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        handleFileUpload(e.dataTransfer.files[0]);
                      }}
                    >
                      <label className="cursor-pointer w-full h-full flex flex-col items-center justify-center z-10 p-8 relative">
                        {status === "idle" && (
                          <div className="space-y-4">
                            <CloudArrowUpIcon className="h-24 w-24 text-blue-500 mx-auto group-hover:text-blue-700 transition-all group-hover:scale-110" />
                            <div>
                              <span className="text-2xl font-bold text-slate-700 group-hover:text-blue-700 block transition-colors">Drop your PDF here</span>
                              <span className="text-sm text-slate-500 mt-2 block">or click to browse files</span>
                            </div>
                          </div>
                        )}
                        {status === "processing" && (
                          <div className="flex flex-col items-center gap-6">
                            <div className="w-16 h-16 border-4 border-blue-700 border-t-transparent rounded-full animate-spin"></div>
                            <div className="text-center">
                              <span className="text-xl text-blue-800 font-bold block mb-1">AI is working its magic</span>
                              <span className="text-sm text-blue-700">Reading, processing, and converting to audio...</span>
                            </div>
                          </div>
                        )}
                        {status === "success" && (
                          <div className="animate-in fade-in zoom-in duration-500">
                             <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                              <SpeakerWaveIcon className="h-10 w-10 text-green-600" />
                            </div>
                            <span className="text-xl text-green-900 font-bold block">Audio Ready!</span>
                          </div>
                        )}
                        <input type="file" className="hidden" accept=".pdf" onChange={(e) => handleFileUpload(e.target.files[0])} disabled={status === "processing"} />
                      </label>
                    </div>

                    {/* AUDIO PLAYER */}
                    {audioUrl && (
                      <div className="mt-8 bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 rounded-2xl p-8 border-2 border-green-200 animate-in fade-in slide-in-from-bottom-6 duration-700 shadow-lg">
                        <div className="flex items-center gap-3 mb-6">
                          <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center"><PlayIcon className="w-6 h-6 text-white" /></div>
                          <div><h3 className="text-green-900 font-bold text-xl">Now Playing</h3><p className="text-green-700 text-sm">Listen or create a quiz from this file</p></div>
                        </div>
                        <audio ref={audioRef} controls src={audioUrl} className="w-full mb-5 rounded-lg shadow-md accent-green-600" />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <a href={audioUrl} download="lecture_audio.mp3" className="flex items-center justify-center gap-3 bg-white text-green-700 font-bold py-4 px-6 rounded-xl shadow-md hover:bg-green-50 transition-all border border-green-200">
                            <ArrowDownTrayIcon className="h-5 w-5" /> Download MP3
                          </a>
                          <button onClick={handleGenerateQuiz} disabled={quizStatus === 'loading'} className="flex items-center justify-center gap-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold py-4 px-6 rounded-xl shadow-md hover:shadow-lg transition-all active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed">
                            {quizStatus === 'loading' ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : <AcademicCapIcon className="h-5 w-5" />}
                            {quizStatus === 'loading' ? "Generating..." : "Generate Quiz & Summary"}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* VISUAL QUIZ */}
                {showQuiz && quizData && (
                  <div className="animate-in fade-in slide-in-from-bottom-10 duration-700 mb-12">
                    <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden border border-blue-300/40">
                      <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-white">
                        <h2 className="text-3xl font-bold flex items-center gap-3"><SparklesIcon className="w-8 h-8 text-blue-200" /> Lecture Summary</h2>
                        <p className="text-blue-100 mt-2">Key takeaways generated by AI</p>
                      </div>
                      <div className="p-8 border-b border-blue-200">
                        <div className="prose prose-lg text-slate-700 leading-relaxed bg-blue-100 p-6 rounded-2xl border border-blue-300">{quizData.summary}</div>
                      </div>
                      <div className="p-8 bg-blue-50">
                        <h3 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2"><AcademicCapIcon className="w-7 h-7 text-blue-700" /> Knowledge Check</h3>
                        <div className="space-y-6">
                          {quizData.quiz.map((q, idx) => (
                            <div key={idx} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                              <p className="font-bold text-lg text-slate-800 mb-4"><span className="text-blue-600 mr-2">{idx + 1}.</span>{q.question}</p>
                              <div className="grid grid-cols-1 gap-3">
                                {q.options.map((opt, i) => (
                                  <button key={i} onClick={(e) => {
                                      const isCorrect = opt === q.answer;
                                      const btn = e.currentTarget;
                                      btn.parentElement.childNodes.forEach(child => child.classList.remove('ring-2', 'ring-green-500', 'bg-green-50', 'ring-red-500', 'bg-red-50'));
                                      if(isCorrect) { btn.classList.add('ring-2', 'ring-green-500', 'bg-green-50'); } 
                                      else { btn.classList.add('ring-2', 'ring-red-500', 'bg-red-50'); }
                                    }}
                                    className="text-left p-4 rounded-xl border border-slate-200 hover:bg-blue-50 hover:border-blue-300 transition-all flex items-center justify-between group"
                                  >
                                    <span className="font-medium text-slate-600 group-hover:text-blue-900">{opt}</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* PAGE 2: BLIND MODE (Audio Learning) */}
            {currentPage === 'blind-mode' && (
               <div className="max-w-4xl mx-auto text-center py-10 animate-in fade-in zoom-in duration-500">
                 <div className="inline-flex items-center gap-2 bg-blue-400/20 backdrop-blur-sm px-4 py-2 rounded-full border border-blue-400/40 mb-8">
                    <EyeSlashIcon className="w-4 h-4 text-blue-700" />
                    <span className="text-sm text-blue-800 font-medium">Audio Learning Mode</span>
                  </div>
                  
                  <h1 className="text-5xl font-black text-blue-900 mb-6">Blind Mode Quiz</h1>
                  <p className="text-xl text-blue-800 mb-12 max-w-2xl mx-auto">
                    Interact with your study material using only your voice. 
                    The AI will read questions aloud and listen for your answers.
                  </p>

                  {/* Start Card */}
                  <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-12 shadow-2xl border border-blue-300/40">
                     <div className="mb-8">
                        <div className={`w-32 h-32 rounded-full flex items-center justify-center mx-auto mb-6 transition-all duration-500 ${blindModeStatus === 'running' ? 'bg-blue-200 animate-pulse ring-4 ring-blue-400' : 'bg-slate-100'}`}>
                           {blindModeStatus === 'running' ? (
                             <SpeakerWaveIcon className="w-16 h-16 text-blue-700" />
                           ) : (
                             <MicrophoneIcon className="w-16 h-16 text-slate-400" />
                           )}
                        </div>
                        <h3 className="text-2xl font-bold text-slate-800">
                          {blindModeStatus === 'running' ? "Quiz is Running..." : "Ready to Start"}
                        </h3>
                        <p className="text-slate-600 mt-2">
                          {blindModeStatus === 'running' 
                            ? "Listen to your computer speakers and speak clearly." 
                            : "Make sure you have uploaded a PDF in the 'Visual Learning' tab first."}
                        </p>
                     </div>

                     <button 
                       onClick={handleStartBlindMode}
                       disabled={blindModeStatus === 'running'}
                       className={`w-full max-w-md mx-auto py-5 px-8 rounded-2xl text-xl font-bold text-white transition-all shadow-xl hover:scale-105 active:scale-95
                         ${blindModeStatus === 'running' 
                           ? 'bg-slate-400 cursor-not-allowed' 
                           : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 shadow-blue-400/40'}`}
                     >
                       {blindModeStatus === 'running' ? "Quiz in Progress" : "Start Voice Quiz"}
                     </button>
                  </div>

                  {/* Results Card */}
                  {blindQuizResults && (
                    <div className="mt-12 animate-in fade-in slide-in-from-bottom-10 duration-1000 text-left">
                        <div className="bg-white/80 backdrop-blur-xl rounded-3xl overflow-hidden shadow-2xl border border-blue-300/40">
                          <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-center text-white">
                              <h2 className="text-3xl font-black mb-2 flex items-center justify-center gap-3">
                                <AcademicCapIcon className="w-8 h-8 text-blue-200"/> 
                                Quiz Results
                              </h2>
                              <div className="text-6xl font-black tracking-tighter my-4 bg-white/10 inline-block px-8 py-2 rounded-2xl border border-white/20">
                                {blindQuizResults.score} / {blindQuizResults.total}
                              </div>
                              <p className="text-blue-100 text-lg font-medium">Great effort! Here is the breakdown:</p>
                          </div>

                          <div className="p-8 bg-blue-50 space-y-6">
                              {blindQuizResults.questions.map((q, idx) => (
                                <div key={idx} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                                    <div className="flex gap-4">
                                      <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 text-cyan-700 rounded-full flex items-center justify-center font-bold">
                                          {idx + 1}
                                      </div>
                                      <div className="flex-1">
                                          <h4 className="text-lg font-bold text-slate-800 mb-4">{q.q}</h4>
                                          <div className="grid gap-2">
                                            {q.options.map((opt, i) => {
                                                const letters = ["A", "B", "C", "D"];
                                                const letter = letters[i];
                                                const isCorrect = letter === q.correct;
                                                return (
                                                  <div key={i} className={`p-3 rounded-xl border flex items-center gap-3 transition-colors
                                                      ${isCorrect 
                                                        ? 'bg-blue-100 border-blue-400 text-blue-900 font-bold shadow-sm' 
                                                        : 'bg-white border-slate-200 text-slate-500'
                                                      }`}>
                                                      <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold border
                                                        ${isCorrect ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-100 border-slate-300 text-slate-400'}`}>
                                                        {letter}
                                                      </span>
                                                      <span className="flex-1">{opt}</span>
                                                      {isCorrect && <CheckCircleIcon className="w-6 h-6 text-blue-600 ml-auto" />}
                                                  </div>
                                                )
                                            })}
                                          </div>
                                      </div>
                                    </div>
                                </div>
                              ))}
                          </div>
                        </div>
                    </div>
                  )}
               </div>
            )}

            {/* PLACEHOLDERS */}
            {/* PAGE 3: AUDIO TO TEXT (Transcription) */}
            {currentPage === 'audio-to-text' && (
              <div className="max-w-4xl mx-auto animate-in fade-in zoom-in duration-500">
                <div className="text-center mb-12 space-y-4">
                  <div className="inline-flex items-center gap-2 bg-blue-400/20 backdrop-blur-sm px-4 py-2 rounded-full border border-blue-400/40 mb-4">
                    <MicrophoneIcon className="w-4 h-4 text-blue-700" />
                    <span className="text-sm text-blue-800 font-medium">Live Voice to Text</span>
                  </div>
                  <h1 className="text-5xl lg:text-6xl font-black tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-blue-900 via-blue-700 to-blue-900">
                    Voice Transcription
                  </h1>
                  <p className="text-lg text-blue-800 max-w-2xl mx-auto">
                    Record with your microphone and convert speech into text, powered by Vosk.
                  </p>
                </div>

                <div className="grid lg:grid-cols-1 gap-8 mb-8">
                  <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-blue-300/40">
                    
                    {/* RECORDING CONTROLS */}
                    <div className="mb-10">
                      <div className="flex flex-col sm:flex-row gap-4 justify-center items-stretch sm:items-center mb-8">
                        <button
                          onClick={startRecording}
                          disabled={isRecording || transcriptStatus === "processing"}
                          className={`flex items-center justify-center gap-2 font-bold py-4 px-8 rounded-xl transition-all shadow-lg text-white text-lg
                            ${isRecording || transcriptStatus === "processing"
                              ? 'bg-slate-400 cursor-not-allowed'
                              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 hover:scale-105 active:scale-95'}`}
                        >
                          <MicrophoneIcon className="w-6 h-6" />
                          Start recording
                        </button>

                        <button
                          onClick={stopRecording}
                          disabled={!isRecording}
                          className={`flex items-center justify-center gap-2 font-bold py-4 px-8 rounded-xl transition-all shadow-lg text-slate-700 text-lg border-2
                            ${!isRecording
                              ? 'bg-slate-200 border-slate-300 cursor-not-allowed text-slate-400'
                              : 'bg-slate-100 border-slate-300 hover:bg-slate-200 hover:scale-105 active:scale-95'}`}
                        >
                          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                            <rect x="6" y="6" width="8" height="8" />
                          </svg>
                          Stop
                        </button>
                      </div>

                      {/* RECORDING INDICATOR */}
                      {isRecording && (
                        <div className="text-center mb-6">
                          <div className="flex items-center justify-center gap-3 text-lg font-bold text-blue-800 bg-blue-100 py-3 px-6 rounded-xl inline-block w-full sm:w-auto">
                            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                            Recording: {Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}
                          </div>
                        </div>
                      )}

                      {/* PROCESSING INDICATOR */}
                      {transcriptStatus === "processing" && (
                        <div className="text-center mb-6">
                          <div className="flex items-center justify-center gap-3 text-lg font-bold text-blue-800 bg-blue-100 py-3 px-6 rounded-xl inline-block w-full sm:w-auto">
                            <div className="w-4 h-4 border-2 border-blue-700 border-t-transparent rounded-full animate-spin"></div>
                            Transcribing...
                          </div>
                        </div>
                      )}
                    </div>

                    {/* LAST RECORDING SECTION */}
                    {lastRecordingUrl && (
                      <div className="mb-10 pb-10 border-b border-blue-300">
                        <div className="flex items-center gap-3 mb-4">
                          <svg className="w-5 h-5 text-blue-700" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                          </svg>
                          <h3 className="text-blue-900 font-bold text-lg">Last recording</h3>
                        </div>
                        <audio 
                          controls 
                          src={lastRecordingUrl} 
                          className="w-full rounded-lg shadow-md border border-blue-300 accent-blue-700"
                        />
                      </div>
                    )}

                    {/* TRANSCRIPT SECTION */}
                    <div>
                      <div className="flex items-center gap-3 justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <DocumentTextIcon className="w-5 h-5 text-blue-700" />
                          <h3 className="text-blue-900 font-bold text-lg">Transcript</h3>
                        </div>
                        {transcriptText && (
                          <button
                            onClick={copyTranscript}
                            className="text-xs sm:text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors"
                          >
                            Copy
                          </button>
                        )}
                      </div>
                      
                      <div className={`min-h-40 p-6 rounded-xl border-2 transition-all ${
                        transcriptText 
                          ? 'border-blue-400 bg-blue-100 text-slate-700' 
                          : 'border-slate-300 bg-slate-50 text-slate-400'
                      }`}>
                        {transcriptText ? (
                          <p className="text-base leading-relaxed whitespace-pre-wrap">{transcriptText}</p>
                        ) : (
                          <p className="text-center py-8">Transcript will appear here after you finish recording.</p>
                        )}
                      </div>

                      {transcriptStatus === "error" && (
                        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                          ⚠️ Error transcribing audio. Please try again.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {currentPage === 'sign-language' && (
              <div className="max-w-4xl mx-auto text-center py-20">
                 <HandRaisedIcon className="w-24 h-24 text-blue-600 mx-auto mb-6 opacity-50" />
                 <h1 className="text-4xl font-bold text-blue-900 mb-4">Coming Soon</h1>
                 <p className="text-blue-700">Sign language interpretation is under development.</p>
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
      `}</style>
    </div>
  );
}

export default App;