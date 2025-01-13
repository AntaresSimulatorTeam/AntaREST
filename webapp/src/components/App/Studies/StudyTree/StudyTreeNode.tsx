import { memo } from "react";
import { StudyTreeNodeProps } from "./types";
import TreeItemEnhanced from "@/components/common/TreeItemEnhanced";
import { t } from "i18next";

export default memo(function StudyTreeNode({
  studyTreeNode,
  parentId,
  onNodeClick,
}: StudyTreeNodeProps) {
  const isLoadingFolder =
    studyTreeNode.hasChildren && studyTreeNode.children.length === 0;
  const id = parentId
    ? `${parentId}/${studyTreeNode.name}`
    : studyTreeNode.name;

  if (isLoadingFolder) {
    return (
      <TreeItemEnhanced
        itemId={id}
        label={studyTreeNode.name}
        onClick={() => onNodeClick(id, studyTreeNode)}
      >
        <TreeItemEnhanced
          itemId={id + "loading"}
          label={t("studies.tree.fetchFolderLoading")}
        />
      </TreeItemEnhanced>
    );
  }
  return (
    <TreeItemEnhanced
      itemId={id}
      label={studyTreeNode.name}
      onClick={() => onNodeClick(id, studyTreeNode)}
    >
      {studyTreeNode.children.map((child) => (
        <StudyTreeNode
          key={`${id}/${child.name}`}
          studyTreeNode={child}
          parentId={id}
          onNodeClick={onNodeClick}
        />
      ))}
    </TreeItemEnhanced>
  );
});
