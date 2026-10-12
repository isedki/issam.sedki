import type { Metadata } from "next";
import Link from "next/link";
import { Schibsted_Grotesk, JetBrains_Mono } from "next/font/google";
import { DOCX, REPO, resume } from "@/lib/resume";
import "./globals.css";

const sans = Schibsted_Grotesk({ variable: "--font-sans", subsets: ["latin"] });
const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Issam Sedki, PhD",
  description: resume.headline + ". A resume built as code, validated against regressions on every change.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <header className="topbar">
          <div className="topbar-inner">
            <Link href="/" className="brand">Issam Sedki</Link>
            <nav aria-label="Main">
              <Link href="/">Resume</Link>
              <Link href="/how-its-built">How it&apos;s built</Link>
              <a href={REPO}>Source</a>
              <a href={DOCX} className="button">Download .docx</a>
            </nav>
          </div>
        </header>
        {children}
        <footer className="footer">
          <p>
            Generated from <a href={`${REPO}/blob/main/resume/content.json`}>resume/content.json</a>. Every
            deploy passes the <Link href="/how-its-built">validation pipeline</Link> first.
          </p>
        </footer>
      </body>
    </html>
  );
}
