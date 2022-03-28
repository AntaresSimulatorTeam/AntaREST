import { StudyTree } from './utils';

export const colors = [
  '#24CF9D',
  '#F3C918',
  '#E317DA',
  '#00B2FF', // '#A5B6C7',
  '#de1d4d',
  '#ded41d',
  '#56B667',
  '#793467',
  '#039944',
  '#297887',
  '#77A688',
  '#227878',
  '#676045',
];

export const TILE_SIZE_X = 50;
export const TILE_SIZE_Y = 60;
export const TILE_SIZE_X_2 = TILE_SIZE_X / 2;
export const TILE_SIZE_Y_2 = TILE_SIZE_Y / 2;

export const CIRCLE_RADIUS = 16;
export const DCX = TILE_SIZE_X_2;
export const DCY = TILE_SIZE_Y - CIRCLE_RADIUS;
export const STROKE_WIDTH = 4;
export const STROKE_WIDTH_2 = STROKE_WIDTH / 2;

export const RECT_X_SPACING = 12;
export const RECT_Y_SPACING = 12;
export const RECT_Y_SPACING_2 = RECT_Y_SPACING / 2;
export const RECT_DECORATION = 3;
export const TEXT_SPACING = 10;
export const TEXT_SIZE = 20;
export const TEXT_SIZE_2 = TEXT_SIZE / 2;
export const ZOOM_OUT = 1.2;
export const MIN_WIDTH = 350;
export const RECT_TEXT_WIDTH = 350;
export const DEPTH_OFFSET = 1;
export const CURVE_OFFSET = 4;

export const fakeTree : StudyTree = {
  name: 'Root',
  attributes: {
    id: 'root',
    modificationDate: Date.now().toString(),
  },
  drawOptions: {
    depth: 5,
    nbAllChildrens: 8,
  },
  children: [
    {
      name: 'Node 1',
      attributes: {
        id: 'node1',
        modificationDate: Date.now().toString(),
      },
      drawOptions: {
        depth: 4,
        nbAllChildrens: 3,
      },
      children: [
        {
          name: 'Node 1.1',
          attributes: {
            id: 'node1.1',
            modificationDate: Date.now().toString(),
          },
          drawOptions: {
            depth: 3,
            nbAllChildrens: 2,
          },
          children: [
            {
              name: 'Node 1.1.1',
              attributes: {
                id: 'node1.1.1',
                modificationDate: Date.now().toString(),
              },
              drawOptions: {
                depth: 2,
                nbAllChildrens: 1,
              },
              children: [
                {
                  name: 'Node 1.1.1.1',
                  attributes: {
                    id: 'node1.1.1.1',
                    modificationDate: Date.now().toString(),
                  },
                  drawOptions: {
                    depth: 1,
                    nbAllChildrens: 0,
                  },
                  children: [

                  ],
                },
              ],
            },
          ],
        },
      ],
    },
    {
      name: 'Node 2',
      attributes: {
        id: 'node2',
        modificationDate: Date.now().toString(),
      },
      drawOptions: {
        depth: 1,
        nbAllChildrens: 0,
      },
      children: [

      ],
    },
    {
      name: 'Node 3',
      attributes: {
        id: 'node3',
        modificationDate: Date.now().toString(),
      },
      drawOptions: {
        depth: 1,
        nbAllChildrens: 0,
      },
      children: [

      ],
    },
    {
      name: 'Node 4',
      attributes: {
        id: 'node4',
        modificationDate: Date.now().toString(),
      },
      drawOptions: {
        depth: 2,
        nbAllChildrens: 1,
      },
      children: [
        {
          name: 'Node 4.1',
          attributes: {
            id: 'node4.1',
            modificationDate: Date.now().toString(),
          },
          drawOptions: {
            depth: 1,
            nbAllChildrens: 0,
          },
          children: [

          ],
        },
      ],
    },
  ],
};

export default {};
