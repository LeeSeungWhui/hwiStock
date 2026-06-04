/**
 * 파일명: layout.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 앱 전역 레이아웃
 */
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import AppShell from "./AppShell";
import LANG_KO from "./lang.ko";
import SharedHydrator from "./common/store/SharedHydrator";
import { loadFrontendConfig } from "./common/config/frontendConfig.server";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: LANG_KO.layout.metadataTitle,
  description: LANG_KO.layout.metadataDescription,
};

/**
 * @description 전역 config를 로드한 뒤 SharedHydrator/AppShell을 포함한 루트 레이아웃을 구성. 입력/출력 계약을 함께 명시
 * @returns {Promise<JSX.Element>}
 */
const RootLayout = async ({ children }) => {

  const frontendConfigObj = await loadFrontendConfig()
  return (
    <html lang="ko">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <SharedHydrator config={frontendConfigObj} />
        <AppShell>
          <div className="bg-gray-50 text-gray-950 min-h-screen">{children}</div>
        </AppShell>
      </body>
    </html>
  );
}

export default RootLayout;
