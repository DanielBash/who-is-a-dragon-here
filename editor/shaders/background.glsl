uniform vec3 color;      // star tint
uniform int time;        // milliseconds
uniform vec2 mouse;      // mouse position in pixels

// ============================================================
// SETTINGS (tweak here)
// ============================================================

const float STAR_DENSITY        = 50.0;
const float STAR_PROBABILITY   = 0.72;

const float STAR_SIZE_MIN      = 0.002;
const float STAR_SIZE_MAX      = 0.005;

const float MOUSE_RADIUS       = 1.0;    // influence radius (uv space)
const float MOUSE_STRENGTH     = 0.038;  // base attraction strength

const float DEPTH_MIN          = 0.35;
const float DEPTH_MAX          = 1.0;

const float BACKGROUND_INTENS  = 0.015;
const float BACKGROUND_WAVE    = 0.002;

// ============================================================

// ---------- hash ----------
float hash21(vec2 p) {
    p = fract(p * vec2(234.34, 851.73));
    p += dot(p, p + 34.45);
    return fract(p.x * p.y);
}

// ---------- smooth radial glow ----------
float radialGlow(vec2 p, vec2 c, float r) {
    float d = length(p - c);
    float x = d / r;
    return exp(-x * x * 4.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // ---------- normalized coords ----------
    vec2 uv = fragCoord / iResolution.xy;
    uv = uv * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;

    // ---------- mouse (same space as uv) ----------
    vec2 m = mouse / iResolution.xy;
    m = m * 2.0 - 1.0;
    m.x *= iResolution.x / iResolution.y;

    float t = float(time) * 0.00005;

    // ---------- background ----------
    vec3 col = color * BACKGROUND_INTENS;
    col += vec3(BACKGROUND_WAVE) *
           sin(vec3(1.2, 1.7, 2.1) * t + uv.xyx * 3.0);

    // ---------- star field ----------
    vec2 grid = uv * STAR_DENSITY;
    vec2 cell = floor(grid);

    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {

            vec2 id = cell + vec2(x, y);
            float rnd = hash21(id);

            if (rnd < STAR_PROBABILITY) continue;

            // base position
            vec2 pos = id + vec2(
                hash21(id + 13.1),
                hash21(id + 91.7)
            );
            pos /= STAR_DENSITY;

            // depth
            float depth = mix(DEPTH_MIN, DEPTH_MAX, hash21(id + 7.7));

            // size
            float size = mix(STAR_SIZE_MIN, STAR_SIZE_MAX, rnd) * depth;

            // ---------- mouse attraction (size-aware) ----------
            vec2 toMouse = m - pos;
            float dist = length(toMouse);

            float falloff = smoothstep(MOUSE_RADIUS, 0.0, dist);

            // Bigger stars = heavier = less pull
            float mass = size / STAR_SIZE_MAX;   // 0..1
            float inertia = 1.0 - mass;          // big → small movement

            pos += normalize(toMouse) *
                   falloff *
                   MOUSE_STRENGTH *
                   depth *
                   inertia;

            // twinkle
            float tw = sin(t * (1.0 + rnd * 2.0) + rnd * 10.0);
            tw = 0.6 + 0.4 * tw;

            // glow
            float g = radialGlow(uv, pos, size) * tw;

            // color variation
            vec3 starCol = mix(
                vec3(1.0, 0.95, 0.85),
                vec3(0.75, 0.85, 1.0),
                rnd
            );

            col += starCol * g * depth * 1.2;
        }
    }

    // ---------- tonemap ----------
    col = 1.0 - exp(-col);
    col = pow(col, vec3(0.9));

    fragColor = vec4(col, 1.0);
}
