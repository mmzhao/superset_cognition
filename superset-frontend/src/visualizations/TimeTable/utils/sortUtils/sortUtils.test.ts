/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { sortNumberWithMixedTypes } from './sortUtils';

const createRow = (sortValues: Record<string, number | null>) => ({
  original: { sortValues },
});

// eslint-disable-next-line no-restricted-globals -- TODO: Migrate from describe blocks
describe('sortNumberWithMixedTypes', () => {
  test('should sort numbers in ascending order', () => {
    const rowA = createRow({ col: 10 });
    const rowB = createRow({ col: 20 });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBeLessThan(0);
  });

  test('should handle equal values', () => {
    const rowA = createRow({ col: 15 });
    const rowB = createRow({ col: 15 });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBe(0);
  });

  test('should handle null values', () => {
    const rowA = createRow({ col: null });
    const rowB = createRow({ col: 10 });

    // null is treated as smallest
    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBeLessThan(0);
  });

  test('should handle both null values', () => {
    const rowA = createRow({ col: null });
    const rowB = createRow({ col: null });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBe(0);
  });

  test('should handle negative numbers', () => {
    const rowA = createRow({ col: -10 });
    const rowB = createRow({ col: 5 });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBeLessThan(0);
  });

  test('should handle zero values', () => {
    const rowA = createRow({ col: 0 });
    const rowB = createRow({ col: 10 });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBeLessThan(0);
  });

  test('should handle missing sortValues gracefully', () => {
    const rowA = { original: {} };
    const rowB = createRow({ col: 10 });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBeLessThan(0);
  });

  test('should handle missing column key in sortValues', () => {
    const rowA = createRow({ other: 5 });
    const rowB = createRow({ col: 10 });

    expect(sortNumberWithMixedTypes(rowA, rowB, 'col')).toBeLessThan(0);
  });

  test('should sort by the correct column', () => {
    const rowA = createRow({ col1: 100, col2: 1 });
    const rowB = createRow({ col1: 1, col2: 100 });

    // Sorting by col1: A (100) > B (1) → positive
    expect(sortNumberWithMixedTypes(rowA, rowB, 'col1')).toBeGreaterThan(0);
    // Sorting by col2: A (1) < B (100) → negative
    expect(sortNumberWithMixedTypes(rowA, rowB, 'col2')).toBeLessThan(0);
  });
});
