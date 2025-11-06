import { useEffect } from 'react';

interface ToastProps {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
}

export default function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div 
      className="fixed bottom-6 right-6 z-50 animate-slide-up"
      role="alert"
    >
      <div className={`px-6 py-3 rounded border-2 border-white ${
        type === 'success' ? 'bg-white text-black' : 'bg-black text-white'
      } font-medium shadow-lg`}>
        {message}
      </div>
    </div>
  );
}
