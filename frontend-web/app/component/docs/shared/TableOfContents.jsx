/**
 * 파일명: TableOfContents.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 컴포넌트 문서 목차 (경량 버전)
 */
import LANG_KO from "../../lang.ko";

const tocItems = [
  {
    id: "dataclass",
    label: LANG_KO.view.tocLabels.dataclass,
    children: [
      { id: "dataclass-easyobj", label: LANG_KO.view.tocLabels.dataclassEasyObj },
      { id: "dataclass-easylist", label: LANG_KO.view.tocLabels.dataclassEasyList },
    ],
  },
  {
    id: "buttons",
    label: LANG_KO.view.tocLabels.buttons,
    children: [
      { id: "button-variants", label: LANG_KO.view.tocLabels.buttonVariants },
      { id: "button-sizes", label: LANG_KO.view.tocLabels.buttonSizes },
    ],
  },
  {
    id: "icons",
    label: LANG_KO.view.tocLabels.icons,
    children: [{ id: "icon-basic", label: LANG_KO.view.tocLabels.iconBasic }],
  },
  {
    id: "inputs",
    label: LANG_KO.view.tocLabels.inputs,
    children: [
      { id: "input-basic", label: LANG_KO.view.tocLabels.inputBasic },
      { id: "input-mask", label: LANG_KO.view.tocLabels.inputMask },
      { id: "input-filter", label: LANG_KO.view.tocLabels.inputFilter },
      { id: "input-advanced", label: LANG_KO.view.tocLabels.inputAdvanced },
    ],
  },
  {
    id: "textareas",
    label: LANG_KO.view.tocLabels.textareas,
    children: [
      { id: "textarea-basic", label: LANG_KO.view.tocLabels.textareaBasic },
      { id: "textarea-states", label: LANG_KO.view.tocLabels.textareaStates },
    ],
  },
  {
    id: "selects",
    label: LANG_KO.view.tocLabels.selects,
    children: [
      { id: "select-basic", label: LANG_KO.view.tocLabels.selectBasic },
      { id: "select-states", label: LANG_KO.view.tocLabels.selectStates },
    ],
  },
  {
    id: "checkboxes",
    label: LANG_KO.view.tocLabels.checkboxes,
    children: [
      { id: "checkbox-basic", label: LANG_KO.view.tocLabels.checkboxBasic },
      { id: "checkbox-variants", label: LANG_KO.view.tocLabels.checkboxVariants },
    ],
  },
  {
    id: "checkbuttons",
    label: LANG_KO.view.tocLabels.checkbuttons,
    children: [
      { id: "checkbutton-basic", label: LANG_KO.view.tocLabels.checkbuttonBasic },
      { id: "checkbutton-variants", label: LANG_KO.view.tocLabels.checkbuttonVariants },
    ],
  },
  {
    id: "radioboxes",
    label: LANG_KO.view.tocLabels.radioboxes,
    children: [
      { id: "radiobox-basic", label: LANG_KO.view.tocLabels.radioboxBasic },
      { id: "radiobox-variants", label: LANG_KO.view.tocLabels.radioboxVariants },
    ],
  },
  {
    id: "radiobuttons",
    label: LANG_KO.view.tocLabels.radiobuttons,
    children: [
      { id: "radiobutton-basic", label: LANG_KO.view.tocLabels.radiobuttonBasic },
      { id: "radiobutton-variants", label: LANG_KO.view.tocLabels.radiobuttonVariants },
    ],
  },
  {
    id: "switches",
    label: LANG_KO.view.tocLabels.switches,
    children: [
      { id: "switch-basic", label: LANG_KO.view.tocLabels.switchBasic },
      { id: "switch-states", label: LANG_KO.view.tocLabels.switchStates },
    ],
  },
  {
    id: "number-inputs",
    label: LANG_KO.view.tocLabels.numberInputs,
    children: [
      { id: "number-basic", label: LANG_KO.view.tocLabels.numberBasic },
      { id: "number-range", label: LANG_KO.view.tocLabels.numberRange },
      { id: "number-unbound", label: LANG_KO.view.tocLabels.numberUnbound },
    ],
  },
  {
    id: "datetime-inputs",
    label: LANG_KO.view.tocLabels.datetimeInputs,
    children: [
      { id: "date-basic", label: LANG_KO.view.tocLabels.dateBasic },
      { id: "time-basic", label: LANG_KO.view.tocLabels.timeBasic },
    ],
  },
  {
    id: "comboboxes",
    label: LANG_KO.view.tocLabels.comboboxes,
    children: [
      { id: "combobox-basic", label: LANG_KO.view.tocLabels.comboboxBasic },
      { id: "combobox-bound", label: LANG_KO.view.tocLabels.comboboxBound },
      { id: "combobox-multi", label: LANG_KO.view.tocLabels.comboboxMulti },
    ],
  },
  {
    id: "dropdowns",
    label: LANG_KO.view.tocLabels.dropdowns,
    children: [
      { id: "dropdown-basic", label: LANG_KO.view.tocLabels.dropdownBasic },
      { id: "dropdown-styles", label: LANG_KO.view.tocLabels.dropdownStyles },
    ],
  },
  {
    id: "loading",
    label: LANG_KO.view.tocLabels.loading,
    children: [{ id: "loading-basic", label: LANG_KO.view.tocLabels.loadingBasic }],
  },
  {
    id: "alerts",
    label: LANG_KO.view.tocLabels.alerts,
    children: [
      { id: "alert-basic", label: LANG_KO.view.tocLabels.alertBasic },
      { id: "alert-types", label: LANG_KO.view.tocLabels.alertTypes },
    ],
  },
  {
    id: "confirms",
    label: LANG_KO.view.tocLabels.confirms,
    children: [{ id: "confirm-basic", label: LANG_KO.view.tocLabels.confirmBasic }],
  },
  {
    id: "toasts",
    label: LANG_KO.view.tocLabels.toasts,
    children: [{ id: "toast-basic", label: LANG_KO.view.tocLabels.toastBasic }],
  },
  {
    id: "tooltips",
    label: LANG_KO.view.tocLabels.tooltips,
    children: [
      { id: "tooltip-basic", label: LANG_KO.view.tocLabels.tooltipBasic },
      { id: "tooltip-placement", label: LANG_KO.view.tocLabels.tooltipPlacement },
    ],
  },
  {
    id: "badges",
    label: LANG_KO.view.tocLabels.badges,
    children: [
      { id: "badge-basic", label: LANG_KO.view.tocLabels.badgeBasic },
      { id: "badge-variants", label: LANG_KO.view.tocLabels.badgeVariants },
    ],
  },
  {
    id: "stats",
    label: LANG_KO.view.tocLabels.stats,
    children: [{ id: "stat-basic", label: LANG_KO.view.tocLabels.statBasic }],
  },
  {
    id: "skeletons",
    label: LANG_KO.view.tocLabels.skeletons,
    children: [
      { id: "skeleton-text", label: LANG_KO.view.tocLabels.skeletonText },
      { id: "skeleton-card", label: LANG_KO.view.tocLabels.skeletonCard },
    ],
  },
  {
    id: "empties",
    label: LANG_KO.view.tocLabels.empties,
    children: [
      { id: "empty-basic", label: LANG_KO.view.tocLabels.emptyBasic },
      { id: "empty-action", label: LANG_KO.view.tocLabels.emptyAction },
    ],
  },
  {
    id: "cards",
    label: LANG_KO.view.tocLabels.cards,
    children: [
      { id: "card-basic", label: LANG_KO.view.tocLabels.cardBasic },
      { id: "card-layouts", label: LANG_KO.view.tocLabels.cardLayouts },
    ],
  },
  {
    id: "tables",
    label: LANG_KO.view.tocLabels.tables,
    children: [
      { id: "table-basic", label: LANG_KO.view.tocLabels.tableBasic },
      { id: "table-controlled", label: LANG_KO.view.tocLabels.tableControlled },
    ],
  },
  {
    id: "pagination",
    label: LANG_KO.view.tocLabels.pagination,
    children: [
      { id: "pagination-basic", label: LANG_KO.view.tocLabels.paginationBasic },
      { id: "pagination-advanced", label: LANG_KO.view.tocLabels.paginationAdvanced },
    ],
  },
  {
    id: "tabs",
    label: LANG_KO.view.tocLabels.tabs,
    children: [
      { id: "tab-basic", label: LANG_KO.view.tocLabels.tabBasic },
      { id: "tab-variants", label: LANG_KO.view.tocLabels.tabVariants },
    ],
  },
  {
    id: "drawers",
    label: LANG_KO.view.tocLabels.drawers,
    children: [
      { id: "drawer-right", label: LANG_KO.view.tocLabels.drawerRight },
      { id: "drawer-left", label: LANG_KO.view.tocLabels.drawerLeft },
    ],
  },
  {
    id: "modals",
    label: LANG_KO.view.tocLabels.modals,
    children: [
      { id: "modal-basic", label: LANG_KO.view.tocLabels.modalBasic },
      { id: "modal-sizes", label: LANG_KO.view.tocLabels.modalSizes },
    ],
  },
  {
    id: "editors",
    label: LANG_KO.view.tocLabels.editors,
    children: [
      { id: "editor-basic", label: LANG_KO.view.tocLabels.editorBasic },
      { id: "editor-bound", label: LANG_KO.view.tocLabels.editorBound },
    ],
  },
  {
    id: "easychart",
    label: LANG_KO.view.tocLabels.easychart,
    children: [
      { id: "easychart-line", label: LANG_KO.view.tocLabels.easychartLine },
      { id: "easychart-bar", label: LANG_KO.view.tocLabels.easychartBar },
    ],
  },
  {
    id: "pdfviewer",
    label: LANG_KO.view.tocLabels.pdfviewer,
    children: [
      { id: "pdf-basic", label: LANG_KO.view.tocLabels.pdfBasic },
      { id: "pdf-remote", label: LANG_KO.view.tocLabels.pdfRemote },
    ],
  },
];

/**
 * @description 컴포넌트 문서 목차 트리를 렌더링하고 섹션 앵커 링크를 제공
 * @returns {JSX.Element}
 */
const TableOfContents = () => {
  return (
    <section className="bg-white">
      <h2 className="text-xl font-semibold mb-4">{LANG_KO.view.tocLabel}</h2>
      <ul className="space-y-2">
        {tocItems.map((tocItemObj) => (
          <li key={tocItemObj.id}>
            <a
              href={`#${tocItemObj.id}`}
              className="text-blue-600 hover:text-blue-800"
            >
              {tocItemObj.label}
            </a>
            {tocItemObj.children && tocItemObj.children.length > 0 && (
              <ul className="ml-4 mt-1 space-y-1">
                {tocItemObj.children.map((child) => (
                  <li key={child.id}>
                    <a
                      href={`#${child.id}`}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      {child.label}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default TableOfContents;
