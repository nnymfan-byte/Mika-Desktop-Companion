extends Node3D

const STATE_URL := "http://127.0.0.1:8765/api/alya"

var root3d: Node3D
var character: Node3D
var eyes: Array[MeshInstance3D] = []
var mouth: MeshInstance3D
var t := 0.0
var blink := 0.0
var speaking := false
var mood := "happy"
var dragging := false
var drag_offset := Vector2i.ZERO
var state_request: HTTPRequest

func _ready():
    _configure_desktop_window()
    root3d = Node3D.new()
    add_child(root3d)
    _setup_environment()
    _build_alya()
    _setup_state_bridge()
    _place_bottom_right()

func _configure_desktop_window():
    var win := get_window()
    win.borderless = true
    win.always_on_top = true
    win.transparent = true
    win.mouse_passthrough = false
    get_viewport().transparent_bg = true
    RenderingServer.viewport_set_transparent_background(get_viewport().get_viewport_rid(), true)

func _place_bottom_right():
    var area := DisplayServer.screen_get_usable_rect()
    var size := get_window().size
    var pos := area.position + area.size - size - Vector2i(24, 12)
    DisplayServer.window_set_position(pos)

func _setup_environment():
    var env = WorldEnvironment.new()
    var e = Environment.new()
    e.background_mode = Environment.BG_COLOR
    e.background_color = Color(0, 0, 0, 0)
    e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    e.ambient_light_color = Color("#9bb7ff")
    e.ambient_light_energy = 0.8
    e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    env.environment = e
    add_child(env)

    var key = DirectionalLight3D.new()
    key.rotation_degrees = Vector3(-25, -25, 0)
    key.light_energy = 1.4
    key.shadow_enabled = true
    add_child(key)

    var fill = OmniLight3D.new()
    fill.position = Vector3(-2, 2.5, 3)
    fill.light_color = Color("#9bb7ff")
    fill.omni_range = 8
    fill.light_energy = 3.5
    add_child(fill)

    var rim = OmniLight3D.new()
    rim.position = Vector3(2, 2.0, 1)
    rim.light_color = Color("#6d8cff")
    rim.omni_range = 7
    rim.light_energy = 2.2
    add_child(rim)

    var camera = Camera3D.new()
    camera.position = Vector3(0, 1.45, 5.2)
    camera.look_at_from_position(camera.position, Vector3(0, 1.25, 0))
    add_child(camera)

func mat(color: Color, roughness := 0.65) -> StandardMaterial3D:
    var m = StandardMaterial3D.new()
    m.albedo_color = color
    m.roughness = roughness
    return m

func sphere(parent: Node3D, pos: Vector3, scale: Vector3, material: Material) -> MeshInstance3D:
    var n = MeshInstance3D.new()
    var s = SphereMesh.new()
    s.radius = 1.0
    s.height = 2.0
    n.mesh = s
    n.position = pos
    n.scale = scale
    n.material_override = material
    parent.add_child(n)
    return n

func cyl(parent: Node3D, pos: Vector3, scale: Vector3, material: Material) -> MeshInstance3D:
    var n = MeshInstance3D.new()
    var c = CylinderMesh.new()
    c.top_radius = 1.0
    c.bottom_radius = 1.0
    c.height = 2.0
    n.mesh = c
    n.position = pos
    n.scale = scale
    n.material_override = material
    parent.add_child(n)
    return n

func _build_alya():
    character = Node3D.new()
    character.position = Vector3(0, -0.35, 0)
    root3d.add_child(character)

    var skin = mat(Color("#f2d8d8"))
    var hair = mat(Color("#c2cad8"), 0.48)
    var blue = mat(Color("#5d8cff"), 0.25)
    var dark = mat(Color("#161b2c"))
    var hoodie = mat(Color("#34446d"))
    var white = mat(Color("#f4f7ff"))

    cyl(character, Vector3(0,0.85,0), Vector3(0.72,0.78,0.45), hoodie)
    sphere(character, Vector3(0,1.45,0), Vector3(0.72,0.78,0.68), skin)

    sphere(character, Vector3(0,1.63,-0.02), Vector3(0.79,0.72,0.73), hair)
    sphere(character, Vector3(-0.66,1.35,0), Vector3(0.20,0.65,0.22), hair)
    sphere(character, Vector3(0.66,1.35,0), Vector3(0.20,0.65,0.22), hair)

    eyes.append(sphere(character, Vector3(-0.27,1.48,-0.66), Vector3(0.12,0.19,0.06), blue))
    eyes.append(sphere(character, Vector3(0.27,1.48,-0.66), Vector3(0.12,0.19,0.06), blue))
    mouth = sphere(character, Vector3(0,1.25,-0.69), Vector3(0.12,0.035,0.025), dark)

    cyl(character, Vector3(-0.12,1.05,-0.48), Vector3(0.025,0.32,0.025), white)
    cyl(character, Vector3(0.12,1.05,-0.48), Vector3(0.025,0.32,0.025), white)

    var left = cyl(character, Vector3(-0.72,0.75,0), Vector3(0.20,0.62,0.20), hoodie)
    left.rotation_degrees.z = -18
    var right = cyl(character, Vector3(0.72,0.75,0), Vector3(0.20,0.62,0.20), hoodie)
    right.rotation_degrees.z = 18

func _setup_state_bridge():
    state_request = HTTPRequest.new()
    add_child(state_request)
    state_request.request_completed.connect(_on_state_received)
    _poll_state()

func _poll_state():
    if state_request.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
        state_request.request(STATE_URL)
    get_tree().create_timer(0.8).timeout.connect(_poll_state)

func _on_state_received(result, response_code, headers, body):
    if response_code != 200:
        return
    var parsed = JSON.parse_string(body.get_string_from_utf8())
    if parsed is Dictionary:
        if parsed.has("mood"):
            mood = str(parsed["mood"])
        if parsed.has("speaking"):
            speaking = bool(parsed["speaking"])
        _apply_mood()

func _apply_mood():
    var m := "happy"
    if mood in ["annoyed", "surprised", "shy", "sleepy", "hype"]:
        m = mood
    if mouth:
        var material := mouth.material_override as StandardMaterial3D
        if material:
            material.albedo_color = Color("#6d86ff") if m in ["happy", "hype", "shy"] else Color("#28304a")
    if character:
        var target := 0.0
        if m == "annoyed":
            target = -0.06
        elif m == "shy":
            target = 0.045
        elif m == "sleepy":
            target = -0.025
        character.rotation.z = lerp(character.rotation.z, target, 0.18)

func _process(delta):
    t += delta
    if character:
        character.position.y = -0.35 + sin(t * 1.8) * 0.035
        character.rotation.y = sin(t * 0.55) * 0.07
        if mouth:
            mouth.position.y = 1.25 + (sin(t * 15.0) * 0.022 if speaking else 0.0)
            mouth.scale.y = 0.09 if speaking else 0.035

    blink += delta
    if blink > 3.0:
        var close := clamp((blink - 3.0) * 11.0, 0.0, 1.0)
        for e in eyes:
            e.scale.y = lerp(0.19, 0.025, close)
        if blink > 3.16:
            blink = 0.0
    else:
        for e in eyes:
            e.scale.y = 0.19

func _input(event):
    if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        get_tree().quit()

    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed:
            dragging = true
            drag_offset = DisplayServer.window_get_position() - Vector2i(event.position)
        else:
            dragging = false

    if event is InputEventMouseMotion and dragging:
        DisplayServer.window_set_position(drag_offset + Vector2i(event.position))
