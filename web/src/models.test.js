import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CampaignViewModel, StudentTakeaway, newPractice} from './models.js';

const campaign = JSON.parse(readFileSync(new URL('./campaign.json', import.meta.url)));
test('campaign presentation derives total, weekly misses and recovery from inputs', () => {
  const model = new CampaignViewModel(campaign);
  assert.equal(model.final.cumulative_attendance, 183);
  assert.equal(model.metWeeks, 7);
  assert.deepEqual(model.missedWeeks.map(row => row.week), [3]);
  assert.deepEqual(model.recoveredWeeks.map(row => row.week), [4]);
  const changed = structuredClone(campaign);
  changed.weekly.at(-1).cumulative_attendance = 190;
  assert.equal(new CampaignViewModel(changed).final.cumulative_attendance, 190);
});
test('final review closes the campaign and does not invent a ninth seminar', () => {
  const model = new CampaignViewModel(campaign);
  assert.match(model.nextCheck(7), /Week 8/);
  assert.match(model.nextCheck(8), /closeout/);
  assert.doesNotMatch(model.nextCheck(8), /Week 9|before.*seminar/);
  assert.equal(model.decision(3).week, 3);
});
test('sample default and partially filled notes are never represented as completed evidence', () => {
  const practice = newPractice('Community');
  const takeaway = new StudentTakeaway({direction: 'Data', scenario: 'Community', practice, plan: null, minutes: 30});
  assert.equal(takeaway.ready, false);
  assert.match(takeaway.text(), /Work in progress/);
  assert.match(takeaway.text(), /Not ready/);
  practice.answers = {assumption: 'A', evidence: 'E', keep: 'K', change: 'C', explain: 'X'};
  assert.equal(takeaway.ready, false);
  practice.reviewed = true;
  practice.evidenceReviewed = true;
  assert.equal(takeaway.ready, true);
  assert.match(takeaway.text(), /Reviewed a sample AI-assisted/);
  practice.prompt = '';
  assert.equal(takeaway.ready, false);
});
test('practice drafts are independent between scenarios', () => {
  const community = newPractice('Community');
  const career = newPractice('Career');
  community.answers.change = 'My change';
  assert.equal(career.answers.change, '');
  assert.notEqual(community.prompt, career.prompt);
});
