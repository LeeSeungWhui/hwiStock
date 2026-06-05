"use client";

/**
 * 파일명: dashboard/tasks/view.jsx
 * 설명: hwiStock 읽기 전용 감시 로그 뷰(CSR 목록 조회)
 */

import { useEffect, useMemo, useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { normalizePageConfig } from "@/app/lib/runtime/pageData";
import Badge from "@/app/lib/component/Badge";
import Button from "@/app/lib/component/Button";
import Card from "@/app/lib/component/Card";
import EasyTable from "@/app/lib/component/EasyTable";
import Input from "@/app/lib/component/Input";
import Pagination from "@/app/lib/component/Pagination";
import Select from "@/app/lib/component/Select";
import { apiJSON } from "@/app/lib/runtime/api";
import { safeJsonParse } from "@/app/lib/runtime/json";
import EasyObj from "@/app/lib/dataset/EasyObj";
import { useEasyList } from "@/app/lib/dataset/EasyList";
import { PAGE_CONFIG } from "./initData";
import LANG_KO from "./lang.ko";

const PAGE_SIZE = 10;
const DEFAULT_SORT = "at_desc";

const getSearchParamText = (searchParams, key) => (
  String(searchParams?.get(key) || "").trim()
);

const toTagList = (value) => {
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value !== "string" || !value.trim()) return [];
  const parsedValue = safeJsonParse(value, null);
  if (Array.isArray(parsedValue)) return parsedValue.filter(Boolean).map(String);
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
};

const toAuditRows = (responsePayload) => {
  const auditRows = responsePayload?.result?.auditLog;
  if (!Array.isArray(auditRows)) return [];
  return auditRows.map((entry, index) => {
    const level = String(entry?.level || "info").trim().toLowerCase();
    const code = String(entry?.code || "AUDIT_EVENT").trim();
    const at = String(entry?.at || "").trim();
    const message = String(entry?.message || "").trim();
    const tagList = toTagList(entry?.tags);
    return {
      id: `${at || "audit"}-${code}-${index}`,
      at: at || "-",
      level: level || "info",
      code,
      message: message || "-",
      tags: tagList,
    };
  });
};

const filterAuditRows = ({ auditRows, keyword, status }) => {
  const keywordText = String(keyword || "").trim().toLowerCase();
  const statusText = String(status || "").trim().toLowerCase();
  return auditRows.filter((entry) => {
    const matchesStatus = !statusText || entry.level === statusText;
    if (!matchesStatus) return false;
    if (!keywordText) return true;
    return [
      entry.at,
      entry.level,
      entry.code,
      entry.message,
      ...(entry.tags || []),
    ]
      .join(" ")
      .toLowerCase()
      .includes(keywordText);
  });
};

const sortAuditRows = ({ auditRows, sort }) => {
  const sortText = String(sort || DEFAULT_SORT).trim().toLowerCase();
  const nextRows = [...auditRows];
  nextRows.sort((leftEntry, rightEntry) => {
    if (sortText === "at_asc") {
      return String(leftEntry.at).localeCompare(String(rightEntry.at));
    }
    if (sortText === "code_asc") {
      return String(leftEntry.code).localeCompare(String(rightEntry.code));
    }
    if (sortText === "code_desc") {
      return String(rightEntry.code).localeCompare(String(leftEntry.code));
    }
    if (sortText === "level_asc") {
      return String(leftEntry.level).localeCompare(String(rightEntry.level));
    }
    return String(rightEntry.at).localeCompare(String(leftEntry.at));
  });
  return nextRows;
};

const TasksView = () => {

  /* 1. 상수 ======================================================================================================================= */
  const statusFilterList = LANG_KO.initData.statusFilterList;
  const sortFilterList = LANG_KO.initData.sortFilterList;
  const allowedStatus = useMemo(
    () => new Set(statusFilterList.map((statusFilterItem) => statusFilterItem.value).filter(Boolean)),
    [statusFilterList],
  );
  const allowedSort = useMemo(
    () => new Set(sortFilterList.map((sortFilterItem) => sortFilterItem.value)),
    [sortFilterList],
  );
  const statusBadgeMapObj = {
    info: "neutral",
    warn: "warning",
    warning: "warning",
    error: "danger",
  };

  /* 2. 데이터 ======================================================================================================================= */
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const pageMode = normalizePageConfig(PAGE_CONFIG).MODE;
  const pageApi = PAGE_CONFIG.API || {};
  const hasListEndpoint = Boolean(pageApi.list);
  const listEndpointPath = typeof pageApi.list === "string"
    ? pageApi.list
    : String(pageApi.list?.path || "");

  const initialKeyword = getSearchParamText(searchParams, "q");
  const initialStatusCandidate = getSearchParamText(searchParams, "status").toLowerCase();
  const initialSortCandidate = getSearchParamText(searchParams, "sort").toLowerCase();
  const initialPageCandidate = Number.parseInt(getSearchParamText(searchParams, "page"), 10);

  const ui = EasyObj({
    keyword: initialKeyword,
    status: allowedStatus.has(initialStatusCandidate) ? initialStatusCandidate : "",
    sort: allowedSort.has(initialSortCandidate) ? initialSortCandidate : DEFAULT_SORT,
    page: Number.isFinite(initialPageCandidate) && initialPageCandidate > 0 ? initialPageCandidate : 1,
    isLoading: true,
    errorMessage: "",
    errorRequestId: "",
  });
  const auditRowList = useEasyList([]);
  const taskMetaObj = EasyObj({ totalCount: 0 });
  const didInitialLoadRef = useRef(false);
  const taskTotalText = LANG_KO.view.action.totalCountTemplate.replace(
    "{total}",
    taskMetaObj.totalCount.toLocaleString("ko-KR"),
  );
  const pageCount = Math.max(1, Math.ceil(taskMetaObj.totalCount / PAGE_SIZE));

  /* 3. UI ========================================================================================================================= */
  const tableColumnList = [
    {
      key: "at",
      header: LANG_KO.view.table.atHeader,
      width: 120,
      render: (row) => <span className="font-mono text-xs text-gray-700">{row?.at || LANG_KO.view.misc.dateUnknown}</span>,
    },
    {
      key: "level",
      header: LANG_KO.view.table.levelHeader,
      width: 120,
      render: (row) => (
        <Badge variant={statusBadgeMapObj[row?.level] || "neutral"} pill>
          {LANG_KO.view.statusLabelMap[row?.level] || row?.level || LANG_KO.view.misc.noData}
        </Badge>
      ),
    },
    {
      key: "code",
      header: LANG_KO.view.table.codeHeader,
      width: 180,
      render: (row) => <span className="font-mono text-xs text-gray-800">{row?.code || LANG_KO.view.misc.noData}</span>,
    },
    {
      key: "message",
      header: LANG_KO.view.table.messageHeader,
      align: "left",
      width: "2fr",
      render: (row) => <span className="text-gray-900">{row?.message || LANG_KO.view.misc.noData}</span>,
    },
    {
      key: "tags",
      header: LANG_KO.view.table.tagsHeader,
      align: "left",
      width: "2fr",
      render: (row) => {
        const tagList = row?.tags || [];
        if (!tagList.length) return <span className="text-gray-400">{LANG_KO.view.misc.dateUnknown}</span>;
        return (
          <div className="flex flex-wrap gap-1">
            {tagList.map((tag) => (
              <Badge key={`${row?.id || "audit"}-${tag}`} variant="outline" pill>
                {tag}
              </Badge>
            ))}
          </div>
        );
      },
    },
  ];

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 7. 함수 ======================================================================================================================= */
  const buildTasksQueryString = (options = {}) => {
    const {
      keyword = "",
      status = "",
      sort = DEFAULT_SORT,
      page = 1,
    } = options;
    const taskQueryParams = new URLSearchParams();
    const keywordText = String(keyword || "").trim();
    const statusText = String(status || "").trim().toLowerCase();
    const sortText = String(sort || DEFAULT_SORT).trim().toLowerCase();
    const pageNum = Number.parseInt(String(page || 1), 10);

    if (keywordText) taskQueryParams.set("q", keywordText);
    if (allowedStatus.has(statusText)) taskQueryParams.set("status", statusText);
    if (allowedSort.has(sortText) && sortText !== DEFAULT_SORT) {
      taskQueryParams.set("sort", sortText);
    }
    if (Number.isFinite(pageNum) && pageNum > 1) {
      taskQueryParams.set("page", String(pageNum));
    }
    return taskQueryParams.toString();
  };

  const syncBrowserQuery = ({ nextKeyword, nextStatus, nextSort, nextPage }) => {
    if (!pathname) return;
    const queryString = buildTasksQueryString({
      keyword: nextKeyword,
      status: nextStatus,
      sort: nextSort,
      page: nextPage,
    });
    const href = queryString ? `${pathname}?${queryString}` : pathname;
    router.replace(href, { scroll: false });
  };

  const loadTasks = async (options = {}) => {
    const {
      nextKeyword = ui.keyword,
      nextStatus = ui.status,
      nextSort = ui.sort,
      nextPage = ui.page,
      syncQuery = true,
    } = options;
    if (!hasListEndpoint || !listEndpointPath) {
      ui.errorMessage = LANG_KO.view.error.listEndpointMissing;
      ui.errorRequestId = "";
      auditRowList.copy([]);
      taskMetaObj.totalCount = 0;
      ui.isLoading = false;
      return;
    }
    const taskQueryParams = new URLSearchParams();
    taskQueryParams.set("page", String(nextPage));
    taskQueryParams.set("size", String(PAGE_SIZE));
    taskQueryParams.set("sort", nextSort || DEFAULT_SORT);
    if (String(nextKeyword || "").trim()) taskQueryParams.set("q", String(nextKeyword).trim());
    if (nextStatus) taskQueryParams.set("status", nextStatus);
    const queryString = taskQueryParams.toString();
    const requestPath = queryString ? `${listEndpointPath}?${queryString}` : listEndpointPath;
    const requestSpec = typeof pageApi.list === "string" || !pageApi.list || typeof pageApi.list !== "object"
      ? requestPath
      : { ...pageApi.list, path: requestPath };

    ui.isLoading = true;
    ui.errorMessage = "";
    ui.errorRequestId = "";
    try {
      const taskResponse = await apiJSON(requestSpec);
      const auditRows = toAuditRows(taskResponse);
      const filteredRows = filterAuditRows({
        auditRows,
        keyword: nextKeyword,
        status: nextStatus,
      });
      const sortedRows = sortAuditRows({ auditRows: filteredRows, sort: nextSort });
      const total = sortedRows.length;
      const pageNum = Math.max(1, Number.parseInt(String(nextPage || 1), 10) || 1);
      const sliceStart = (pageNum - 1) * PAGE_SIZE;
      const pageRows = sortedRows.slice(sliceStart, sliceStart + PAGE_SIZE);
      auditRowList.copy(pageRows);
      taskMetaObj.totalCount = total;
      ui.page = pageNum;
      ui.sort = nextSort || DEFAULT_SORT;
      ui.status = nextStatus || "";
      ui.keyword = String(nextKeyword || "");
      if (syncQuery) {
        syncBrowserQuery({
          nextKeyword,
          nextStatus,
          nextSort: nextSort || DEFAULT_SORT,
          nextPage: pageNum,
        });
      }
    } catch (err) {
      auditRowList.copy([]);
      taskMetaObj.totalCount = 0;
      ui.errorMessage = err?.message || LANG_KO.view.error.listLoadFailed;
      ui.errorRequestId = err?.requestId || "";
    } finally {
      ui.isLoading = false;
    }
  };

  /* 8. useEffect ================================================================================================================== */
  useEffect(() => {
    if (didInitialLoadRef.current) return;
    didInitialLoadRef.current = true;
    loadTasks({
      nextKeyword: ui.keyword,
      nextStatus: ui.status,
      nextSort: ui.sort,
      nextPage: ui.page,
      syncQuery: false,
    });
  }, []);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="space-y-3" data-page-mode={pageMode} data-readonly="true">
      {ui.errorMessage && (
        <section aria-label={LANG_KO.view.error.listLoadFailed}>
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            <div>{ui.errorMessage}</div>
            {ui.errorRequestId && (
              <div className="mt-1 text-xs text-red-700/80">
                {LANG_KO.view.error.requestIdLabel}: {ui.errorRequestId}
              </div>
            )}
          </div>
        </section>
      )}

      <Card title={LANG_KO.view.card.filterTitle}>
        <p className="mb-3 text-sm text-gray-500">{LANG_KO.view.card.filterSubtitle}</p>
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <div className="flex-1">
            <Input
              dataObj={ui}
              dataKey="keyword"
              placeholder={LANG_KO.view.search.keywordPlaceholder}
            />
          </div>
          <div className="w-full md:w-48">
            <Select
              dataObj={ui}
              dataKey="status"
              dataList={statusFilterList}
            />
          </div>
          <div className="w-full md:w-52">
            <Select
              dataObj={ui}
              dataKey="sort"
              dataList={sortFilterList}
            />
          </div>
          <Button
            variant="outline"
            onClick={() =>
              loadTasks({
                nextKeyword: ui.keyword,
                nextStatus: ui.status,
                nextSort: ui.sort,
                nextPage: 1,
              })
            }
            loading={ui.isLoading}
            className="w-full sm:w-auto"
          >
            {LANG_KO.view.search.searchButton}
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              ui.keyword = "";
              ui.status = "";
              ui.sort = DEFAULT_SORT;
              loadTasks({
                nextKeyword: "",
                nextStatus: "",
                nextSort: DEFAULT_SORT,
                nextPage: 1,
              });
            }}
            disabled={ui.isLoading}
            className="w-full sm:w-auto"
          >
            {LANG_KO.view.search.resetButton}
          </Button>
        </div>
      </Card>

      <Card title={LANG_KO.view.card.tableTitle}>
        <EasyTable
          dataList={auditRowList}
          loading={ui.isLoading}
          columns={tableColumnList}
          pageSize={PAGE_SIZE}
          empty={LANG_KO.view.table.emptyFallback}
          rowKey={(row, index) => row?.id ?? index}
        />
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-gray-600">
            {taskTotalText}
          </div>
          <Pagination
            page={ui.page}
            pageCount={pageCount}
            onChange={(nextPage) =>
              loadTasks({
                nextKeyword: ui.keyword,
                nextStatus: ui.status,
                nextSort: ui.sort,
                nextPage,
              })
            }
          />
        </div>
      </Card>
    </div>
  );
};

export default TasksView;
