import React from 'react';

interface QRCodeProps {
  data: string;
  size?: number;
}

export const QRCode: React.FC<QRCodeProps> = ({ data, size = 200 }) => {
  // Using a public API for QR generation to avoid heavy dependencies in this demo environment
  // 白色背景，黑色二维码，更清晰易扫
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}&bgcolor=FF-FF-FF&color=00-00-00&margin=1`;

  return (
    <div className="p-4 bg-white rounded-xl border-2 border-galaxy-light/30 inline-block shadow-2xl shadow-galaxy-accent/30">
      <img 
        src={qrUrl} 
        alt="Scan to Join" 
        width={size} 
        height={size}
        className="rounded-lg"
      />
    </div>
  );
};