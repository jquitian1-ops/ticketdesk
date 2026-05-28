import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkillWall Live",
  description: "Comparte tus skills y dale like a las de otros participantes."
};

export default function RootLayout({
  children
}: {
  readonly children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
