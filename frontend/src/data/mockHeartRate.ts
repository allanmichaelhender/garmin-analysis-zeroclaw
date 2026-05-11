export const mockHeartRateData = {
  "1": Array.from({ length: 180 }, (_, i) => {
    // Simulate warm-up, tempo, cool-down pattern
    if (i < 30) return 120 + Math.random() * 10; // Warm-up
    if (i < 120) return 145 + Math.random() * 15; // Tempo
    return 130 + Math.random() * 10; // Cool-down
  }),
  "2": Array.from({ length: 270 }, (_, i) => {
    if (i < 40) return 110 + Math.random() * 10;
    if (i < 200) return 130 + Math.random() * 15;
    return 120 + Math.random() * 10;
  }),
  "3": Array.from({ length: 210 }, (_, i) => {
    if (i < 35) return 125 + Math.random() * 10;
    if (i < 150) return 150 + Math.random() * 15;
    return 135 + Math.random() * 10;
  }),
  "4": Array.from({ length: 180 }, (_, i) => {
    if (i < 30) return 120 + Math.random() * 10;
    if (i < 120) return 135 + Math.random() * 15;
    return 125 + Math.random() * 10;
  }),
  "5": Array.from({ length: 240 }, (_, i) => {
    if (i < 40) return 125 + Math.random() * 10;
    if (i < 180) return 148 + Math.random() * 15;
    return 135 + Math.random() * 10;
  }),
};
