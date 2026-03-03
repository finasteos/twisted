import { Handle, Position } from '@xyflow/react';
import { Upload, Type, Camera, Mic, X, Check, Play, Square, FileText, Video } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export function DropNode({ data, id }: any) {
  const [mode, setMode] = useState<'select' | 'text' | 'camera' | 'record'>('select');
  const [evidence, setEvidence] = useState<{ id: string; type: string; preview: string }[]>([]);
  const [textInput, setTextInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (mode === 'camera' || mode === 'record') {
      navigator.mediaDevices.getUserMedia({ video: true, audio: mode === 'record' })
        .then((s) => {
          setStream(s);
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
        })
        .catch(err => console.error("Media error:", err));
    } else {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
        setStream(null);
      }
    }
    return () => {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
    };
  }, [mode]);

  const addEvidence = (type: string, preview: string, content?: string) => {
    setEvidence(prev => [...prev, { id: Date.now().toString(), type, preview, content }]);
    setMode('select');
  };

  const removeEvidence = (evidenceId: string) => {
    setEvidence(prev => prev.filter(e => e.id !== evidenceId));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      Array.from(e.target.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
          addEvidence('file', file.name, event.target?.result as string);
        };
        reader.readAsText(file);
      });
    }
  };

  const handleTextSubmit = () => {
    if (textInput.trim()) {
      addEvidence('text', textInput.substring(0, 30) + (textInput.length > 30 ? '...' : ''), textInput);
      setTextInput('');
    }
  };

  const takePhoto = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(videoRef.current, 0, 0);
        addEvidence('photo', 'Captured Image');
      }
    }
  };

  const toggleRecord = () => {
    if (isRecording) {
      setIsRecording(false);
      addEvidence('video', 'Live Recording');
    } else {
      setIsRecording(true);
    }
  };

  return (
    <div className="brutalist-card p-6 w-[32rem] min-h-[200px] flex flex-col space-y-6 relative">
      <Handle type="target" position={Position.Top} />
      
      {data.wittyText && (
        <div className="bg-[#111] text-white p-4 font-mono text-sm uppercase font-bold">
          {data.wittyText}
        </div>
      )}

      {mode === 'select' && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <button onClick={() => fileInputRef.current?.click()} className="brutalist-button py-4 flex flex-col items-center justify-center space-y-2 group">
              <Upload size={24} className="group-hover:-translate-y-1 transition-transform" />
              <span className="text-xs">Drop Files</span>
            </button>
            <input type="file" multiple className="hidden" ref={fileInputRef} onChange={handleFileSelect} />

            <button onClick={() => setMode('text')} className="brutalist-button py-4 flex flex-col items-center justify-center space-y-2 group">
              <Type size={24} className="group-hover:-translate-y-1 transition-transform" />
              <span className="text-xs">Paste Text</span>
            </button>

            <button onClick={() => setMode('camera')} className="brutalist-button py-4 flex flex-col items-center justify-center space-y-2 group">
              <Camera size={24} className="group-hover:-translate-y-1 transition-transform" />
              <span className="text-xs">Take Photo</span>
            </button>

            <button onClick={() => setMode('record')} className="brutalist-button py-4 flex flex-col items-center justify-center space-y-2 group">
              <Mic size={24} className="group-hover:-translate-y-1 transition-transform" />
              <span className="text-xs">Live Record</span>
            </button>
          </div>

          {evidence.length > 0 && (
            <div className="space-y-2 mt-4">
              <h3 className="font-black uppercase text-sm border-b-2 border-[#111] pb-1">Collected Evidence</h3>
              {evidence.map(item => (
                <div key={item.id} className="flex items-center justify-between border-2 border-[#111] p-2 bg-[#f4f4f0]">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    {item.type === 'file' && <FileText size={16} />}
                    {item.type === 'text' && <Type size={16} />}
                    {item.type === 'photo' && <Camera size={16} />}
                    {item.type === 'video' && <Video size={16} />}
                    <span className="font-mono text-xs truncate">{item.preview}</span>
                  </div>
                  <button onClick={() => removeEvidence(item.id)} className="hover:bg-[#111] hover:text-white p-1 transition-colors">
                    <X size={16} />
                  </button>
                </div>
              ))}
              <button 
                onClick={() => data.onAnalyze && data.onAnalyze(id, evidence)}
                className="brutalist-button w-full py-3 mt-4 flex items-center justify-center space-x-2 bg-[#00ff88] text-[#111] border-[#111] hover:bg-[#111] hover:text-[#00ff88]"
              >
                <Play size={18} fill="currentColor" />
                <span>Analyze Evidence</span>
              </button>
            </div>
          )}
        </>
      )}

      {mode === 'text' && (
        <div className="flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b-2 border-[#111] pb-2">
            <h3 className="font-black uppercase">Paste Text</h3>
            <button onClick={() => setMode('select')}><X size={20} /></button>
          </div>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            className="w-full h-32 border-2 border-[#111] p-2 font-mono text-sm resize-none outline-none focus:bg-[#f4f4f0]"
            placeholder="Paste clipboard text here..."
            autoFocus
          />
          <button onClick={handleTextSubmit} disabled={!textInput.trim()} className="brutalist-button py-2 flex items-center justify-center space-x-2">
            <Check size={16} />
            <span>Save Text</span>
          </button>
        </div>
      )}

      {mode === 'camera' && (
        <div className="flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b-2 border-[#111] pb-2">
            <h3 className="font-black uppercase">Take Photo</h3>
            <button onClick={() => setMode('select')}><X size={20} /></button>
          </div>
          <div className="border-4 border-[#111] bg-black relative aspect-video overflow-hidden">
            <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
          </div>
          <button onClick={takePhoto} className="brutalist-button py-3 flex items-center justify-center space-x-2">
            <Camera size={18} />
            <span>Capture</span>
          </button>
        </div>
      )}

      {mode === 'record' && (
        <div className="flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b-2 border-[#111] pb-2">
            <h3 className="font-black uppercase">Live Record</h3>
            <button onClick={() => setMode('select')}><X size={20} /></button>
          </div>
          <div className="border-4 border-[#111] bg-black relative aspect-video overflow-hidden">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            {isRecording && (
              <div className="absolute top-4 right-4 flex items-center space-x-2 bg-black/50 px-2 py-1 border border-red-500">
                <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                <span className="text-red-500 font-mono text-xs font-bold">REC</span>
              </div>
            )}
          </div>
          <button 
            onClick={toggleRecord} 
            className={`brutalist-button py-3 flex items-center justify-center space-x-2 ${isRecording ? 'bg-red-500 text-white border-red-500 hover:bg-white hover:text-red-500' : ''}`}
          >
            {isRecording ? <Square size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
            <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
          </button>
        </div>
      )}

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
