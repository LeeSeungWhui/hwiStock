"use client";

/**
 * 파일명: EasyChart.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Recharts 기반 대시보드 차트 카드 래퍼
 */

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Cell,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useEffect, useRef, useState } from "react";
import Card from "./Card";
import Skeleton from "./Skeleton";
import Empty from "./Empty";
import { COMMON_COMPONENT_LANG_KO } from "@/app/common/i18n/lang.ko";

const chartColorList = [
  "#2563eb",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ef4444",
  "#0ea5e9",
  "#14b8a6",
];
const defaultMarginObj = { top: 12, right: 20, left: 10, bottom: 12 };
const donutMarginObj = { top: 36, right: 16, bottom: 24, left: 16 };
const chartHeightClassMap = {
  160: "h-40",
  180: "h-[180px]",
  200: "h-[200px]",
  220: "h-[220px]",
  240: "h-[240px]",
  260: "h-[260px]",
  280: "h-[280px]",
  300: "h-[300px]",
  320: "h-[320px]",
  360: "h-[360px]",
};
const heightBucketList = [180, 220, 260, 300, 320];

/**
 * @description 배열 또는 EasyList류 차트 입력을 실제 배열로 평탄화하는 데이터 어댑터.
 * 처리 규칙: 배열은 그대로 반환하고, list-like는 size/get 기반으로 새 배열을 구성한다.
 * @updated 2026-04-18
 */
const readChartList = (chartList) => {
  if (Array.isArray(chartList)) return chartList;
  const hasChartListShape =
    Boolean(chartList) &&
    (typeof chartList.size === "function" || Array.isArray(chartList));
  if (hasChartListShape) {
    const chartItemCount = typeof chartList.size === "function" ? chartList.size() : 0;
    const chartItemList = [];
    for (let chartIndex = 0; chartIndex < chartItemCount; chartIndex += 1) {
      chartItemList.push(
        typeof chartList.get === "function" ? chartList.get(chartIndex) : undefined,
      );
    }
    return chartItemList;
  }
  return [];
};

/**
 * @description 카드 스타일을 유지한 Recharts 래퍼 컴포넌트.
 * @param {Object} props
 * 처리 규칙: 데이터/시리즈 입력을 정규화하고 loading/error/empty 상태 우선순위로 본문 UI를 분기한다.
 * @returns {JSX.Element}
 * @updated 2026-02-28
 */
const EasyChart = ({
  title,
  subtitle,
  dataList,
  data,
  xKey = "label",
  seriesList,
  series,
  type = "line",
  height = 260,
  actions,
  loading = false,
  status,
  errorText,
  empty = COMMON_COMPONENT_LANG_KO.easyChart.empty,
  hideLegend = false,
  pieLabelFontSize = 12,
  xLabelFormatter,
  yLabelFormatter,
  className = "",
  cardProps = {},
}) => {

  const [isClient, setIsClient] = useState(false);
  const chartHostRef = useRef(null);
  const [hostSize, setHostSize] = useState({ width: 0, height: 0 });
  const dataSource = dataList ?? data ?? [];
  const seriesSource = seriesList ?? series ?? [];
  const resolvedSeries = readChartList(seriesSource)
    .map((seriesItemObj, index) => ({
      key: seriesItemObj.seriesId ?? seriesItemObj.key ?? seriesItemObj.dataKey,
      name: seriesItemObj.seriesNm ?? seriesItemObj.name ?? seriesItemObj.label ?? seriesItemObj.dataKey,
      color: seriesItemObj.color || chartColorList[index % chartColorList.length],
      type: seriesItemObj.type || type,
      stackId: seriesItemObj.stackId,
      strokeWidth: seriesItemObj.strokeWidth,
      dot: seriesItemObj.dot,
    }))
    .filter((seriesItemObj) => seriesItemObj.key);

  const resolvedDataList = readChartList(dataSource);
  const chartCellIndexList = [];
  for (let dataIndex = 0; dataIndex < resolvedDataList.length; dataIndex += 1) {
    chartCellIndexList.push(dataIndex);
  }

  const hasSeries = resolvedSeries.length > 0;
  const chartType = resolvedSeries[0]?.type || type;
  const isPie = chartType === "pie";
  const isDonut = chartType === "donut";
  const isEmpty = resolvedDataList.length === 0 || status === "empty";
  const isLoading = loading || status === "loading";
  const isError = status === "error";
  const isComposed = resolvedSeries.some((seriesItem) => seriesItem.type && seriesItem.type !== type);
  const pieValueKey = resolvedSeries[0]?.key;
  const hasHostSize = hostSize.width > 0 && hostSize.height > 0;
  let parsedHeight = null;
  if (typeof height === "number") {
    if (Number.isFinite(height)) parsedHeight = Math.floor(height);
  } else if (typeof height === "string") {
    const normalizedHeight = height.trim().toLowerCase();
    const heightMatch = normalizedHeight.match(/^(\d+)(px)?$/);
    if (heightMatch) parsedHeight = Number(heightMatch[1]);
  }
  const resolvedHeight = parsedHeight ?? 260;
  const hostTargetHeight = Math.max(0, resolvedHeight);
  const pieTargetHeight = Math.max(180, resolvedHeight);
  const hostBucketKey = heightBucketList.find(
    (heightKey) => hostTargetHeight <= heightKey,
  ) ?? 360;
  const pieBucketKey = heightBucketList.find(
    (heightKey) => pieTargetHeight <= heightKey,
  ) ?? 360;
  const hostHeightClassName = chartHeightClassMap[hostTargetHeight]
    ?? chartHeightClassMap[hostBucketKey];
  const pieHeightClassName = chartHeightClassMap[pieTargetHeight]
    ?? chartHeightClassMap[pieBucketKey];

  /**
   * @description 클라이언트 마운트 후 차트 렌더 가능 상태로 전환
   * 처리 규칙: 최초 마운트에서 setIsClient(true)를 1회 호출한다.
   */
  useEffect(() => {
    setIsClient(true);
  }, []);

  /**
   * @description isClient일 때 ResizeObserver로 차트 호스트 width/height 동기화
   * 처리 규칙: cleanup에서 observer disconnect를 수행한다.
   */
  useEffect(() => {
    if (!isClient) return undefined;
    if (!chartHostRef.current) return undefined;

    /**
     * @description 차트 호스트 DOM 크기를 읽어 내부 width/height 상태를 동기화
     * 처리 규칙: 이전 크기와 동일하면 상태 갱신을 생략해 불필요한 렌더를 방지한다.
     * @updated 2026-02-27
     */
    const updateHostSize = () => {
      if (!chartHostRef.current) return;
      const rect = chartHostRef.current.getBoundingClientRect();
      const nextSizeObj = {
        width: Math.round(rect.width || 0),
        height: Math.round(rect.height || 0),
      };
      setHostSize((prevSize) => {
        if (
          prevSize.width === nextSizeObj.width &&
          prevSize.height === nextSizeObj.height
        ) {
          return prevSize;
        }
        return nextSizeObj;
      });
    };

    updateHostSize();
    if (typeof ResizeObserver === "undefined") {
      const rafId = window.requestAnimationFrame(updateHostSize);
      return () => window.cancelAnimationFrame(rafId);
    }

    const observer = new ResizeObserver(() => {
      updateHostSize();
    });
    observer.observe(chartHostRef.current);
    return () => observer.disconnect();
  }, [isClient, height, isPie, isDonut]);

  let ChartComponent = LineChart;
  if (isComposed && hasSeries) {
    ChartComponent = ComposedChart;
  } else if (type === "bar") {
    ChartComponent = BarChart;
  } else if (type === "area") {
    ChartComponent = AreaChart;
  }
  const seriesNodes = hasSeries
    ? resolvedSeries.map((seriesItem, index) => {
        const seriesKey = seriesItem.key || seriesItem.name || `series-${index}`;
        const seriesPropsObj = {
          name: seriesItem.name,
          dataKey: seriesItem.key,
          stroke: seriesItem.color,
          fill: seriesItem.color,
          strokeWidth: seriesItem.strokeWidth || 2,
        };
        let seriesType = chartType;
        const shouldUseSeriesType = !isPie && !isDonut && isComposed;
        if (shouldUseSeriesType) {
          seriesType = seriesItem.type;
        }
        if (seriesType === "bar") {
          return (
            <Bar
              key={seriesKey}
              {...seriesPropsObj}
              stackId={seriesItem.stackId}
              radius={[4, 4, 0, 0]}
            />
          );
        }
        if (seriesType === "area") {
          return (
            <Area key={seriesKey} {...seriesPropsObj} type="monotone" fillOpacity={0.12} />
          );
        }
        if (seriesType === "pie" || seriesType === "donut") {
          return null;
        }
        return (
          <Line
            key={seriesKey}
            {...seriesPropsObj}
            type="monotone"
            dot={seriesItem.dot ?? false}
            activeDot={{ r: 4 }}
          />
        );
      })
    : null;

  let bodyContent = null;
  if (isLoading) {
    bodyContent = (
      <div className="space-y-4" aria-live="polite">
        <Skeleton variant="text" lines={2} />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  } else if (isError) {
    bodyContent = (
      <div
        className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        role="alert"
      >
        {errorText ||
          COMMON_COMPONENT_LANG_KO.easyChart.loadFailed}
      </div>
    );
  } else if (!hasSeries) {
    bodyContent = (
      <div
        className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
        role="status"
      >
        {COMMON_COMPONENT_LANG_KO.easyChart.seriesRequired}
      </div>
    );
  } else if (!isClient) {
    bodyContent = (
      <div className={`min-w-0 w-full pt-1 ${hostHeightClassName}`.trim()} />
    );
  } else if (isEmpty) {
    bodyContent =
      typeof empty === "string" ? (
        <Empty title={empty} className="bg-gray-50" />
      ) : (
        empty
      );
  } else if (isPie || isDonut) {
    if (!pieValueKey) {
      bodyContent = (
        <div
          className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
          role="status"
        >
          {COMMON_COMPONENT_LANG_KO.easyChart.seriesRequired}
        </div>
      );
    } else {
      bodyContent = (
        <div
          ref={chartHostRef}
          className={`min-w-0 w-full ${pieHeightClassName}`.trim()}
        >
          {hasHostSize ? (
            <PieChart
              width={hostSize.width}
              height={hostSize.height}
              margin={donutMarginObj}
            >
              <Tooltip />
              {!hideLegend && (
                <Legend
                  verticalAlign="bottom"
                  align="center"
                  iconType="circle"
                  iconSize={10}
                />
              )}
              <Pie
                data={resolvedDataList}
                dataKey={pieValueKey}
                nameKey={xKey}
                innerRadius={isDonut ? "55%" : undefined}
                outerRadius={isDonut ? "82%" : "80%"}
                paddingAngle={isDonut ? 3 : 0}
                labelLine={!isDonut}
                label={(pieLabelObj) => {
                  const pct = Math.round((pieLabelObj.percent || 0) * 100);
                  return (
                    <text
                      x={pieLabelObj.x}
                      y={pieLabelObj.y}
                      fill="#374151"
                      fontSize={pieLabelFontSize}
                      textAnchor="middle"
                      dominantBaseline="central"
                    >
                      {`${pieLabelObj.name ?? ""} ${pieLabelObj.value} (${pct}%)`}
                    </text>
                  );
                }}
              >
                {chartCellIndexList.map((dataIndex) => (
                  <Cell
                    key={`cell-${dataIndex}`}
                    fill={
                      resolvedSeries[dataIndex]?.color ||
                      chartColorList[dataIndex % chartColorList.length]
                    }
                    stroke={isDonut ? "#ffffff" : undefined}
                    strokeWidth={isDonut ? 1.4 : undefined}
                  />
                ))}
              </Pie>
            </PieChart>
          ) : null}
        </div>
      );
    }
  } else {
    bodyContent = (
      <div
        ref={chartHostRef}
        className={`min-w-0 w-full ${hostHeightClassName}`.trim()}
      >
        {hasHostSize ? (
          <ChartComponent
            data={resolvedDataList}
            margin={defaultMarginObj}
            width={hostSize.width}
            height={hostSize.height}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey={xKey}
              tickLine={false}
              axisLine={{ stroke: "#e5e7eb" }}
              tickFormatter={xLabelFormatter}
              tick={{ fontSize: 12, fill: "#6b7280" }}
            />
            <YAxis
              tickLine={false}
              axisLine={{ stroke: "#e5e7eb" }}
              tickFormatter={yLabelFormatter}
              tick={{ fontSize: 12, fill: "#6b7280" }}
            />
            <Tooltip
              formatter={(value, name) => [value, name]}
              labelFormatter={xLabelFormatter}
            />
            {!hideLegend && (
              <Legend
                verticalAlign="bottom"
                align="center"
                iconType="circle"
                iconSize={10}
              />
            )}
            {seriesNodes}
          </ChartComponent>
        ) : null}
      </div>
    );
  }

  return (
    <Card
      title={title}
      subtitle={subtitle}
      actions={actions}
      className={`h-full ${className}`.trim()}
      bodyClassName="space-y-2"
      {...cardProps}
    >
      {bodyContent}
    </Card>
  );
};

/**
 * @description Card 래퍼와 상태 분기(loading/error/empty)를 포함한 EasyChart 컴포넌트를 외부에 노출
 * 반환값: EasyChart 컴포넌트 export.
 */
export default EasyChart;
