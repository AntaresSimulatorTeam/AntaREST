/* eslint-disable react/jsx-props-no-spreading */
import React, { useEffect, useMemo, useState } from 'react';
import { Box, styled } from '@mui/material';
import { StudyMetadata, VariantTree } from '../../../../common/types';
import { StudyTree, getTreeNodes } from './utils';
import { scrollbarStyle } from '../../../../theme';
import { CIRCLE_RADIUS, colors, DCX, DCY, DEPTH_OFFSET, fakeTree, MIN_WIDTH, RECT_DECORATION, RECT_TEXT_WIDTH, RECT_X_SPACING, RECT_Y_SPACING, RECT_Y_SPACING_2, STROKE_WIDTH, STROKE_WIDTH_2, TEXT_SIZE, TEXT_SPACING, TILE_SIZE_X, TILE_SIZE_X_2, TILE_SIZE_Y, TILE_SIZE_Y_2, ZOOM_OUT, CURVE_OFFSET } from './treeconfig';

export const SVGCircle = styled(
  'circle',
  { shouldForwardProp: (prop) => prop !== 'hoverColor' },
)<{hoverColor: string }>(({ theme, hoverColor }) => ({
  cursor: 'pointer',
  '&:hover': {
    fill: hoverColor,
  },
}));
export const SVGRect = styled(
  'rect',
  { shouldForwardProp: (prop) => prop !== 'hoverColor' },
)<{hoverColor: string }>(({ theme, hoverColor }) => ({
  cursor: 'pointer',
  '&:hover': {
    fill: hoverColor,
  },
}));

interface Props {
  study: StudyMetadata | undefined;
  parents: Array<StudyMetadata>;
  childrenTree: VariantTree | undefined;
  onClick: (studyId: string) => void;
}

export default function CustomizedTreeView(props: Props) {
  const { study, parents, childrenTree, onClick } = props;
  const [studyTree, setStudyTree] = useState<StudyTree>(fakeTree);

  const RECT_WIDTH = useMemo(() => {
    const { drawOptions } = studyTree;
    const { depth } = drawOptions;
    return Math.max(TILE_SIZE_X * (depth + DEPTH_OFFSET), MIN_WIDTH);
  }, [studyTree]);

  const treeWidth = RECT_WIDTH + RECT_TEXT_WIDTH + RECT_X_SPACING;

  const treeHeight = useMemo(() => {
    const { drawOptions } = studyTree;
    const { nbAllChildrens } = drawOptions;
    return TILE_SIZE_Y * (nbAllChildrens + 1) + TILE_SIZE_Y_2;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyTree]);

  const buildRecursiveTree = (tree: StudyTree, i = 0, j = 0) : Array<React.ReactNode> => {
    const { drawOptions, name, attributes, children } = tree;
    const { id } = attributes;
    const { nbAllChildrens } = drawOptions;
    const hoverColor = colors[i % colors.length];
    const color = `${hoverColor}FF`;
    const rectColor = `${hoverColor}0D`;
    const rectHoverColor = `${hoverColor}44`;
    const verticalLineColor = `${colors[(i + 1) % colors.length]}`;
    let verticalLineEnd = 0;

    if (children.length > 0) {
      verticalLineEnd = nbAllChildrens - children[children.length - 1].drawOptions.nbAllChildrens;
      // verticalLineEnd = (j + 1 + verticalLineEnd) * TILE_SIZE_Y - CIRCLE_RADIUS;
      verticalLineEnd = (j + verticalLineEnd) * TILE_SIZE_Y + CIRCLE_RADIUS;
    }

    const cx = i * TILE_SIZE_X + DCX;
    const cy = j * TILE_SIZE_Y + DCY;
    let res : Array<React.ReactNode> = [<SVGCircle key={`circle-${i}-${j}`} cx={cx} cy={cy} r={CIRCLE_RADIUS} fill={color} hoverColor={hoverColor} onClick={() => console.log('NODE: ', tree.name)} />,
      <SVGRect key={`rect-${i}-${j}`} x="0" y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2} width={RECT_WIDTH} height={TILE_SIZE_Y - RECT_Y_SPACING} fill={rectColor} hoverColor={rectHoverColor} />,
      <SVGRect key={`rect-for-name-${i}-${j}`} x={RECT_WIDTH + RECT_X_SPACING} y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2} width={RECT_TEXT_WIDTH} height={TILE_SIZE_Y - RECT_Y_SPACING} fill={rectColor} hoverColor={hoverColor} onClick={() => onClick(id)} />,
      <SVGRect key={`rect-for-name-deco-${i}-${j}`} x={RECT_WIDTH + RECT_X_SPACING} y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2} width={RECT_DECORATION} height={TILE_SIZE_Y - RECT_Y_SPACING} fill={hoverColor} hoverColor={hoverColor} />,
      <text key={`name-${i}-${j}`} x={RECT_WIDTH + RECT_X_SPACING + RECT_DECORATION + TEXT_SPACING} y={cy + RECT_Y_SPACING_2} fill="white" fontSize={TEXT_SIZE}>{name}</text>];
    if (verticalLineEnd > 0) { res.push(<path key={`verticalLine-${i}-${j}`} d={`M ${cx} ${cy + CIRCLE_RADIUS} L ${cx} ${verticalLineEnd}`} fill={verticalLineColor} stroke={verticalLineColor} strokeWidth={`${STROKE_WIDTH}`} />); }
    // if (i > 0) { res.push(<path key={`horizontalLine-${i}-${j}`} d={`M ${cx - CIRCLE_RADIUS} ${cy} L ${cx - TILE_SIZE_X - (STROKE_WIDTH_2)} ${cy}`} fill={color} stroke={color} strokeWidth={`${STROKE_WIDTH}`} />); }
    if (i > 0) { res.push(<path key={`horizontalLine-${i}-${j}`} d={`M ${cx - CIRCLE_RADIUS - CURVE_OFFSET},${cy} C ${cx - TILE_SIZE_X},${cy} ${cx - TILE_SIZE_X},${cy} ${cx - TILE_SIZE_X},${cy - TILE_SIZE_Y + 2 * CIRCLE_RADIUS} M ${cx - CIRCLE_RADIUS},${cy} L ${cx - CIRCLE_RADIUS - CURVE_OFFSET},${cy}`} fill="transparent" stroke={color} strokeWidth={`${STROKE_WIDTH}`} />); }

    let recursiveHeight = 1;
    res = res.concat(children.map((elm, index) => {
      if (index === 0) recursiveHeight = j + 1;
      else recursiveHeight = recursiveHeight + children[index - 1].drawOptions.nbAllChildrens + 1;
      return buildRecursiveTree(elm, i + 1, recursiveHeight);
    }));
    return res;
  };

  const renderTree = (tree: StudyTree) : React.ReactNode => {
    const { drawOptions } = tree;
    const { depth, nbAllChildrens } = drawOptions;
    return (
      <svg viewBox={`0 0 ${Math.max(TILE_SIZE_X * (depth + DEPTH_OFFSET), MIN_WIDTH) + RECT_TEXT_WIDTH + RECT_X_SPACING} ${TILE_SIZE_Y * (nbAllChildrens + 1) + TILE_SIZE_Y_2}`}>
        {buildRecursiveTree(tree, 0, 0) }
      </svg>
    );
  };

  useEffect(() => {
    const buildStudyTree = async () => {
      if (study && childrenTree) {
        const tmp = await getTreeNodes(study, parents, childrenTree);
        setStudyTree(tmp);
      }
    };
    buildStudyTree();
  }, [study, parents, childrenTree]);

  return (
    <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="flex-start" sx={{ width: '100%', flexGrow: 1, overflowY: 'auto', ...scrollbarStyle }}>
      <Box minWidth={treeWidth / ZOOM_OUT} minHeight={treeHeight / ZOOM_OUT} display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start">
        {studyTree && renderTree(studyTree)}
      </Box>
      <Box height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center">
        {studyTree && renderTree(studyTree)}
      </Box>
    </Box>
  );
}
