import "i18next";

declare module "i18next" {
  interface CustomTypeOptions {
    returnNull: false; // https://www.i18next.com/overview/typescript#argument-of-type-defaulttfuncreturn-is-not-assignable-to-parameter-of-type-xyz
  }
}
