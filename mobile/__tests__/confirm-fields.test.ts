import {
  CONFIDENCE_THRESHOLD,
  draftLooksSolid,
  fieldNeedsCheck,
  fieldsNeedingCheck,
  formatAcceptedSummary,
  shouldUseSmartConfirm,
} from '../utils/confirmFields';

describe('confirmFields', () => {
  it('flags low-confidence fields', () => {
    expect(
      fieldNeedsCheck('color', { color: 0.5 }, 'navy', 'photo'),
    ).toBe(true);
    expect(
      fieldNeedsCheck('color', { color: 0.95 }, 'navy', 'photo'),
    ).toBe(false);
  });

  it('trusts filled fields without a score', () => {
    expect(fieldNeedsCheck('color', {}, 'navy', 'photo')).toBe(false);
  });

  it('flags empty identity fields', () => {
    expect(fieldNeedsCheck('brand', {}, '', 'photo')).toBe(true);
    expect(fieldNeedsCheck('brand', { brand: 0.94 }, 'Uniqlo', 'label_ocr')).toBe(false);
  });

  it('lists fields needing check', () => {
    const fields = fieldsNeedingCheck(
      { category: 0.97, color: 0.5 },
      { name: 'Tee', category: 'top', color: 'black', brand: '' },
      'photo',
    );
    expect(fields).toContain('color');
    expect(fields).toContain('brand');
    expect(fields).not.toContain('category');
  });

  it('detects solid drafts', () => {
    expect(
      draftLooksSolid(
        { category: 0.97, color: 0.93, subcategory: 0.9 },
        { name: 'Tee', category: 'top', color: 'black', subcategory: 't-shirt', brand: 'Uniqlo' },
        'photo',
      ),
    ).toBe(true);
  });

  it('builds accepted summary', () => {
    const summary = formatAcceptedSummary(
      { color: 'navy', pattern: 'solid', brand: '' },
      ['brand'],
    );
    expect(summary).toContain('navy');
    expect(summary).toContain('solid');
    expect(summary).not.toContain('brand');
  });

  it('smart confirm only for AI sources', () => {
    expect(shouldUseSmartConfirm('photo', false)).toBe(true);
    expect(shouldUseSmartConfirm('manual', false)).toBe(false);
    expect(shouldUseSmartConfirm('photo', true)).toBe(false);
  });

  it('exports threshold', () => {
    expect(CONFIDENCE_THRESHOLD).toBe(0.8);
  });
});
