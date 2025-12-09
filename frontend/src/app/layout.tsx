import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import BackgroundLayout from "../components/BackgroundLayout";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter", // Optional if using CSS variables, but strict CSS used 'Inter' name.
  // Next.js font loader handles class names too if we apply 'inter.className' to body.
});

export const metadata: Metadata = {
  title: "Agent JobSearch",
  description: "Building blocks for data security and compliance",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <BackgroundLayout>
          {children}
        </BackgroundLayout>
      </body>
    </html>
  );
}
