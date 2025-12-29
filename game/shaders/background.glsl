uniform int time;

// ============================================================
// SETTINGS
// ============================================================

const float STAR_DENSITY   = 60.0;
const float STAR_SHARPNESS = 120.0;
const float NEBULA_SCALE   = 2.5;
const float SCROLL_SPEED  = 0.05;

// ============================================================
// HASH
// ============================================================

float hash(vec2 p) {
    p = fract(p * vec2(127.1, 311.7));
    p += dot(p, p + 34.5);
    return fract(p.x * p.y);
}

// ============================================================
// NOISE
// ============================================================

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    vec2 u = f * f * (3.0 - 2.0 * f);

    return mix(a, b, u.x) +
           (c - a) * u.y * (1.0 - u.x) +
           (d - b) * u.x * u.y;
}

// ============================================================
// FBM
// ============================================================

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

// ============================================================
// DOMAIN ROTATION
// ============================================================

mat2 rotate(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

// ============================================================
// STAR SHAPE
// ============================================================

float star(vec2 uv, float seed) {
    float d = length(uv);
    float core = exp(-d * d * STAR_SHARPNESS);

    float spike = abs(uv.x * uv.y);
    spike = exp(-spike * 80.0);

    return core + spike * seed * 0.8;
}

// ============================================================
// MAIN
// ============================================================

void mainImage(out vec4 fragColor, in vec2 fragCoord) {

    vec2 uv = fragCoord / iResolution.xy;
    uv = uv * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;

    float t = float(time) * 0.001 * SCROLL_SPEED;

    vec2 warpedUV = rotate(0.37) * uv;
    warpedUV += 0.15 * vec2(
        fbm(uv * 1.7 + t),
        fbm(uv * 1.3 - t)
    );

    vec2 spaceUV = warpedUV * STAR_DENSITY +
                   vec2(t * 0.7, t * 1.1);

    vec2 cell = floor(spaceUV);
    vec2 local = fract(spaceUV) - 0.5;

    vec2 jitter = vec2(
        hash(cell + 5.1),
        hash(cell + 9.7)
    ) - 0.5;

    local += jitter * 0.35;

    float rnd = hash(cell);

    vec3 col = vec3(0.0);

    if (rnd > 0.995) {

        float size = mix(0.6, 1.6, hash(cell + 3.3));
        float s = star(local * size, rnd);

        vec3 starCol = mix(
            vec3(0.65, 0.75, 1.0),
            vec3(1.0, 0.85, 0.6),
            hash(cell + 11.1)
        );

        col += starCol * s * 3.0;
    }

    float nebula = fbm(warpedUV * NEBULA_SCALE + vec2(0.0, t * 0.4));
    vec3 nebulaCol = vec3(0.15, 0.2, 0.35) * pow(nebula, 2.6);

    col += nebulaCol;

    col = 1.0 - exp(-col);
    col = pow(col, vec3(0.9));

    fragColor = vec4(col, 1.0);
}
