"use client";

/**
 * 파일명: dashboard/tasks/view.jsx
 * 설명: hwiStock 읽기 전용 감시 로그 뷰(CSR 목록 조회)
 */

import { useCallback, useEffect, useMemo } from "react";
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

const TasksView = () => {

  /* 1. 상수 ======================================================================================================================= */
  const pageSize = 10;
  const defaultSort = "reg_dt_desc";
  const statusFilterList = LANG_KO.initData.statusFilterList;
  const sortFilterList = LANG_KO.initData.sortFilterList;
  const allowedStatus = useMemo(
    () => new Set(statusFilterList.map((statusFilterObj) => statusFilterObj.value).filter(Boolean)),
    [statusFilterList],
  );
  const allowedSort = useMemo(
    () => new Set(sortFilterList.map((sortFilterObj) => sortFilterObj.value)),
    [sortFilterList],
  );
  const statusBadgeMapObj = {
    ready: "neutral",
    pending: "warning",
    running: "outline",
    done: "success",
    failed: "danger",
  };

  /* 2. 데이터 ======================================================================================================================= */
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const keywordValue = String(searchParams?.get("q") || "").trim();
  const statusCandidate = String(searchParams?.get("status") || "").trim().toLowerCase();
  const statusValue = allowedStatus.has(statusCandidate) ? statusCandidate : "";
  const sortCandidate = String(searchParams?.get("sort") || "").trim().toLowerCase();
  const sortValue = allowedSort.has(sortCandidate) ? sortCandidate : defaultSort;
  const pageCandidate = Number.parseInt(String(searchParams?.get("page") || ""), 10);
  const pageValue = Number.isFinite(pageCandidate) && pageCandidate > 0 ? pageCandidate : 1;

  const ui = EasyObj({
    keyword: keywordValue,
    status: statusValue,
    sort: sortValue,
    page: pageValue,
    isLoading: true,
    error: null,
  });
  const taskList = useEasyList([]);
  const taskMetaObj = EasyObj({ totalCount: 0 });
  const taskTotalText = LANG_KO.view.action.totalCountTemplate.replace(
    "{total}",
    taskMetaObj.totalCount.toLocaleString("ko-KR"),
  );
  const pageMode = normalizePageConfig(PAGE_CONFIG).MODE;
  const pageApi = PAGE_CONFIG.API || {};
  const hasListEndpoint = Boolean(pageApi.list);

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

  /* 3. UI ========================================================================================================================= */
  const tableColumnList = [
    {
      key: "title",
      header: LANG_KO.view.table.titleHeader,
      align: "left",
      width: "2fr",
      render: (row) => <span className="text-gray-900">{row?.title || LANG_KO.view.misc.noData}</span>,
    },
    {
      key: "status",
      header: LANG_KO.view.table.statusHeader,
      width: 140,
      render: (row) => (
        <Badge variant={statusBadgeMapObj[row?.status] || "neutral"} pill>
          {LANG_KO.view.statusLabelMap[row?.status] || row?.status || LANG_KO.view.misc.noData}
        </Badge>
      ),
    },
    {
      key: "amount",
      header: LANG_KO.view.table.amountHeader,
      width: 140,
      align: "right",
      render: (row) => {
        const amount = Number(row?.amount || 0);
        if (Number.isNaN(amount)) return LANG_KO.view.misc.currencyZero;
        return amount.toLocaleString("ko-KR");
      },
    },
    {
      key: "tags",
      header: LANG_KO.view.table.tagsHeader,
      align: "left",
      width: "2fr",
      render: (row) => {
        const tagList = toTagList(row?.tags) || [];
        if (!tagList.length) return <span className="text-gray-400">{LANG_KO.view.misc.dateUnknown}</span>;
        return (
          <div className="flex flex-wrap gap-1">
            {tagList.map((tag) => (
              <Badge key={`${row?.id || "row"}-${tag}`} variant="outline" pill>
                {tag}
              </Badge>
            ))}
          </div>
        );
      },
    },
    {
      key: "createdAt",
      header: LANG_KO.view.table.createdAtHeader,
      width: 140,
      render: (row) => {
        if (!row?.createdAt) return LANG_KO.view.misc.dateUnknown;
        const createdAtDate = new Date(row.createdAt);
        if (Number.isNaN(createdAtDate.getTime())) return LANG_KO.view.misc.dateUnknown;
        return createdAtDate.toISOString().slice(0, 10);
      },
    },
  ];
  const pageCount = Math.max(1, Math.ceil(taskMetaObj.totalCount / pageSize));

  /* 7. 함수 ======================================================================================================================= */
  const buildTasksQueryString = useCallback((options = {}) => {
    const {
      keyword = "",
      status = "",
      sort = defaultSort,
      page = 1,
    } = options;
    const taskQueryParams = new URLSearchParams();
    const keywordText = String(keyword || "").trim();
    const statusText = String(status || "").trim().toLowerCase();
    const sortText = String(sort || defaultSort).trim().toLowerCase();
    const pageNum = Number.parseInt(String(page || 1), 10);

    if (keywordText) taskQueryParams.set("q", keywordText);
    if (allowedStatus.has(statusText)) taskQueryParams.set("status", statusText);
    if (allowedSort.has(sortText) && sortText !== defaultSort) {
      taskQueryParams.set("sort", sortText);
    }
    if (Number.isFinite(pageNum) && pageNum > 1) {
      taskQueryParams.set("page", String(pageNum));
    }
    return taskQueryParams.toString();
  }, [allowedSort, allowedStatus, defaultSort]);

  const syncBrowserQuery = useCallback(({ nextKeyword, nextStatus, nextSort, nextPage }) => {
    if (!pathname) return;
    const queryString = buildTasksQueryString({
      keyword: nextKeyword,
      status: nextStatus,
      sort: nextSort,
      page: nextPage,
    });
    const href = queryString ? `${pathname}?${queryString}` : pathname;
    router.replace(href, { scroll: false });
  }, [buildTasksQueryString, pathname, router]);

  const loadTasks = useCallback(async (options = {}) => {
    const {
      nextKeyword = ui.keyword,
      nextStatus = ui.status,
      nextSort = ui.sort,
      nextPage = ui.page,
      syncQuery = true,
    } = options;
    if (!hasListEndpoint) {
      ui.error = { message: LANG_KO.view.error.listEndpointMissing };
      taskList.copy([]);
      taskMetaObj.totalCount = 0;
      ui.isLoading = false;
      return;
    }
    const taskQueryParams = new URLSearchParams();
    taskQueryParams.set("page", String(nextPage));
    taskQueryParams.set("size", String(pageSize));
    taskQueryParams.set("sort", nextSort || defaultSort);
    if (nextKeyword?.trim()) taskQueryParams.set("q", nextKeyword.trim());
    if (nextStatus) taskQueryParams.set("status", nextStatus);
    const queryString = taskQueryParams.toString();
    const listPath = typeof pageApi.list === "string" ? pageApi.list : String(pageApi.list?.path || "");
    const requestPath = queryString ? `${listPath}?${queryString}` : listPath;
    const requestSpec = typeof pageApi.list === "string" || !pageApi.list || typeof pageApi.list !== "object"
      ? requestPath
      : { ...pageApi.list, path: requestPath };

    ui.isLoading = true;
    ui.error = null;
    try {
      const taskListResponse = await apiJSON(requestSpec);
      taskList.copy(taskListResponse?.result?.dataTemplateList || []);
      const totalSource = taskListResponse?.count ?? taskListResponse?.result?.listMetaObj?.totalCount ?? taskList.size();
      const total = Number(totalSource || 0);
      taskMetaObj.totalCount = total;
      ui.page = nextPage;
      ui.sort = nextSort || defaultSort;
      if (syncQuery) {
        syncBrowserQuery({
          nextKeyword,
          nextStatus,
          nextSort: nextSort || defaultSort,
          nextPage,
        });
      }
    } catch (err) {
      taskList.copy([]);
      taskMetaObj.totalCount = 0;
      ui.error = {
        message: err?.message || LANG_KO.view.error.listLoadFailed,
        requestId: err?.requestId,
      };
    } finally {
      ui.isLoading = false;
    }
  }, [hasListEndpoint, pageApi.list, syncBrowserQuery, taskList, taskMetaObj, ui]);

  /* 4. 팝업 ======================================================================================================================= */

  // 없음

  /* 5. 기타 ======================================================================================================================= */

  // 없음

  /* 6. 커스텀 훅 =================================================================================================================== */

  // 없음

  /* 8. useEffect ================================================================================================================== */
  useEffect(() => {
    loadTasks({
      nextKeyword: ui.keyword,
      nextStatus: ui.status,
      nextSort: ui.sort,
      nextPage: ui.page,
      syncQuery: false,
    });
  }, [hasListEndpoint, loadTasks, ui.keyword, ui.page, ui.sort, ui.status]);

  /* 9. 내부 컴포넌트 ============================================================================================================== */

  // 없음

  /* 10. 렌더링 ==================================================================================================================== */
  return (
    <div className="space-y-3" data-page-mode={pageMode} data-readonly="true">
      {ui.error?.message && (
        <section aria-label={LANG_KO.view.error.listLoadFailed}>
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            <div>{ui.error.message}</div>
            {ui.error.requestId && (
              <div className="mt-1 text-xs text-red-700/80">
                {LANG_KO.view.error.requestIdLabel}: {ui.error.requestId}
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
              ui.sort = defaultSort;
              loadTasks({
                nextKeyword: "",
                nextStatus: "",
                nextSort: defaultSort,
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
          dataList={taskList}
          loading={ui.isLoading}
          columns={tableColumnList}
          pageSize={pageSize}
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
