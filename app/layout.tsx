import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Curriculum Designer",
  description: "AI-powered curriculum design for English teachers",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}