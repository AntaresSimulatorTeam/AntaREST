import Draft, { ContentState, convertFromHTML, convertToRaw, DraftBlockRenderMap, EditorState } from 'draft-js';
import draftToHtml from 'draftjs-to-html';
import * as Immutable from 'immutable';

export const defaultBlockRenderMap = (): DraftBlockRenderMap => {
  const blockRenderMap = Immutable.Map({
    u: {
      element: 'ins',
    },
    ins: {
      element: 'u',
    },
  });
  return Draft.DefaultDraftBlockRenderMap.merge(blockRenderMap);
};

export const htmlToDraftJs = (data: string, extendedBlockRenderMap?: DraftBlockRenderMap): ContentState => {
  const blocksFromHTML = convertFromHTML(data, undefined, extendedBlockRenderMap);
  return ContentState.createFromBlockArray(
    blocksFromHTML.contentBlocks,
    blocksFromHTML.entityMap,
  );
};

export const DraftJsToHtml = (editorState: EditorState) => {
  const rawContentState = convertToRaw(editorState.getCurrentContent());
  return draftToHtml(
    rawContentState,
  );
};

export default {};
