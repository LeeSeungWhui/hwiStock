"use client";

/**
 * 파일명: sample/dashboard/view.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 공개 샘플 대시보드 페이지 뷰(DB dashboard 연동)
 */

import Link from "next/link";
import EasyChart from "@/app/lib/component/EasyChart";
import EasyTable from "@/app/lib/component/EasyTable";
import Stat from "@/app/lib/component/Stat";
import { PAGE_CONFIG } from "./initData";
import { usePageData } from "@/app/lib/hooks/usePageData";
import LANG_KO from "./lang.ko";

/**
 * @description 공개 샘플 대시보드 화면을 렌더링. 입력/출력 계약을 함께 명시
 * 처리 규칙: KPI/차트/최근 업무 목록은 `/api/v1/sample/dashboard` 응답을 그대로 사용한다.
 * @param {{ initialDataObj?: Object, initialErrorObj?: Object }} props
 */
const DemoDashboardView = ({ initialDataObj, initialErrorObj }) => {

  /* 1. 상수 ======================================================================================================================= */
  const ctaLinkList = [
    { href: "/sample/crud", label: LANG_KO.initData.ctaLabels.crud },
    { href: "/sample/admin", label: LANG_KO.initData.ctaLabels.admin },
  ];

  /* 2. 데이터 ======================================================================================================================= */
  const { mode: pageMode, dataObj, isLoading } = usePageData({
    pageConfig: PAGE_CONFIG,
    initialDataObj,
    initialErrorObj,
  });
  const dashboardResult = dataObj?.dashboard?.result || {};
  const summaryList = dashboardResult?.statusSummaryList || [];
  const trendList = dashboardResult?.trendList || [];
  const recentList = dashboardResult?.recentList || [];
  const totalCount = summaryList.reduce((total, summaryItemObj) => total + Number(summaryItemObj?.count || 0), 0);
  const totalAmount = summaryList.reduce((total, summaryItemObj) => total + Number(summaryItemObj?.amountSum || 0), 0);
  const activeCount = summaryList.reduce((total, summaryItemObj) => {
    const status = String(summaryItemObj?.status || "");
    if (status === "running" || status === "pending") {
      return total + Number(summaryItemObj?.count || 0);
    }
    return total;
  }, 0);
  const statCardList = [
    {
      label: LANG_KO.view.statLabel.totalCount,
      value: totalCount.toLocaleString("ko-KR"),
      deltaType: "neutral",
    },
    {
      label: LANG_KO.view.statLabel.totalAmount,
      value: totalAmount.toLocaleString("ko-KR"),
      deltaType: "neutral",
    },
    {
      label: LANG_KO.view.statLabel.activePending,
      value: activeCount.toLocaleString("ko-KR"),
      deltaType: "neutral",
    },
  ];
  const donutDataList = summaryList.map((summaryItemObj) => ({
    label: LANG_KO.view.statusLabelMap[summaryItemObj?.status] || summaryItemObj?.status || LANG_KO.view.unknown,
    value: Number(summaryItemObj?.count || 0),
  }));
  const tableColumnList = [
    { key: "title", header: LANG_KO.view.table.titleHeader, align: "left", width: "2fr" },
    {
      key: "status",
      header: LANG_KO.view.table.statusHeader,
      width: 120,
      render: (rowItem) =>
        LANG_KO.view.statusLabelMap[rowItem?.status] || rowItem?.status || "-",
    },
    {
      key: "amount",
      header: LANG_KO.view.table.amountHeader,
      width: 140,
      render: (rowItem) => Number(rowItem?.amount || 0).toLocaleString("ko-KR"),
    },
    { key: "createdAt", header: LANG_KO.view.table.createdAtHeader, width: 120 },
  ];

  /* 3. UI ========================================================================================================================= */

  // 없음

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 7. 함수 ======================================================================================================================= */

  // 없음

  /* 8. useEffect ================================================================================================================== */

  // 없음

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="space-y-3" data-page-mode={pageMode}>
      <section className="grid gap-3 md:grid-cols-3">
        {statCardList.map((statCardObj) => (
          <Stat
            key={statCardObj.label}
            {...statCardObj}
            className="p-1"
            value={isLoading ? "..." : statCardObj.value}
          />
        ))}
      </section>

      <section className="grid gap-3 md:grid-cols-2">
        <EasyChart
          title={LANG_KO.view.chart.trendTitle}
          dataList={trendList}
          seriesList={[
            {
              seriesId: "count",
              seriesNm: LANG_KO.view.chart.seriesCount,
              dataKey: "count",
              color: "#2563eb",
            },
            {
              seriesId: "amount",
              seriesNm: LANG_KO.view.chart.seriesAmount,
              dataKey: "amount",
              color: "#10b981",
            },
          ]}
          xKey="label"
          type="line"
          height={180}
          legendFontSize={12}
        />
        <EasyChart
          title={LANG_KO.view.chart.statusTitle}
          dataList={donutDataList}
          seriesList={[
            {
              seriesId: "value",
              seriesNm: LANG_KO.view.chart.seriesCount,
              dataKey: "value",
              type: "donut",
            },
          ]}
          xKey="label"
          height={180}
          legendFontSize={12}
        />
      </section>

      <section className="grid gap-3 lg:grid-cols-[minmax(0,2fr)_280px]">
        <EasyTable
          title={LANG_KO.view.card.recentTitle}
          description={LANG_KO.view.card.recentSubtitle}
          data={recentList}
          columns={tableColumnList}
          loading={isLoading}
          empty={LANG_KO.view.table.empty}
          rowKey={(rowItem, rowIndex) => rowItem?.id ?? rowIndex}
        />
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-gray-900">{LANG_KO.view.quickLinkTitle}</p>
          <div className="mt-3 space-y-2">
            {ctaLinkList.map((ctaLinkObj) => (
              <Link
                key={ctaLinkObj.href}
                href={ctaLinkObj.href}
                className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
              >
                <span>{ctaLinkObj.label}</span>
                <span aria-hidden>→</span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default DemoDashboardView;
