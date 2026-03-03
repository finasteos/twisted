import { FileImage, FileText, Film, FolderDown, Mail, X } from 'lucide-react';
import { useCallback, useRef } from 'react';

interface DropZoneProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

const VALID_EXT = [
  'txt', 'md', 'json', 'xml', 'csv',
  'pdf', 'docx', 'doc',
  'eml', 'msg',
  'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
  'mp4', 'mov', 'avi', 'mkv', 'webm',
  'mp3', 'wav', 'm4a', 'flac',
];

function getFileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'].includes(ext)) return <FileImage size={14} />;
  if (['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(ext)) return <Film size={14} />;
  if (['eml', 'msg'].includes(ext)) return <Mail size={14} />;
  return <FileText size={14} />;
}

export function DropZone({ files, onFilesChange }: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const isValid = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    return VALID_EXT.includes(ext);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();

      const dropped = Array.from(e.dataTransfer.files).filter(isValid);
      const existing = new Set(files.map((f) => f.name));
      const newFiles = dropped.filter((f) => !existing.has(f.name));
      onFilesChange([...files, ...newFiles]);
    },
    [files, onFilesChange]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!e.target.files) return;
      const selected = Array.from(e.target.files).filter(isValid);
      const existing = new Set(files.map((f) => f.name));
      const newFiles = selected.filter((f) => !existing.has(f.name));
      onFilesChange([...files, ...newFiles]);
    },
    [files, onFilesChange]
  );

  const removeFile = useCallback(
    (name: string) => {
      onFilesChange(files.filter((f) => f.name !== name));
    },
    [files, onFilesChange]
  );

  return (
    <div>
      <div
        className={`drop-zone ${files.length > 0 ? '' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          e.currentTarget.classList.add('active');
        }}
        onDragLeave={(e) => {
          e.currentTarget.classList.remove('active');
        }}
        onDrop={(e) => {
          e.currentTarget.classList.remove('active');
          handleDrop(e);
        }}
        onClick={() => inputRef.current?.click()}
      >
        <FolderDown className="icon" />
        <h3>Drop files here</h3>
        <p>Text, PDF, DOCX, Email, Images, Video, Audio — or click to browse</p>

        <input
          ref={inputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          accept={VALID_EXT.map((e) => `.${e}`).join(',')}
        />
      </div>

      {files.length > 0 && (
        <div className="file-list">
          {files.map((f) => (
            <div key={f.name} className="file-chip">
              {getFileIcon(f.name)}
              <span>{f.name}</span>
              <X
                className="remove"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(f.name);
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
