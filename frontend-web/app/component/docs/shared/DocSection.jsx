/**
 * 파일명: DocSection.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: 문서 섹션 래퍼
 */
import LANG_KO from "../../lang.ko";

/**
 * @description 문서 섹션의 제목/설명/본문 영역을 공통 구조로 렌더링
 * @param {{ id: string, title: string, description?: React.ReactNode, children?: React.ReactNode }} props
 * @returns {JSX.Element}
 */
const DocSection = ({ id, title, description, children }) => {

  const titleId = id ? `${id}-title` : undefined;
  return (
    <section id={id} aria-labelledby={titleId} className="mb-12">
      <h2 id={titleId} className="text-2xl font-semibold mb-4">{title}</h2>
      {description && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium mb-2">{LANG_KO.view.descriptionHeading}</h4>
          <div className="text-sm text-gray-600">
            {description}
          </div>
        </div>
      )}
      {children}
    </section>
  );
};

export default DocSection;
