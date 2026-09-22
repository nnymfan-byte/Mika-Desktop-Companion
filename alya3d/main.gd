extends Node3D

var root3d: Node3D
var character: Node3D
var head: Node3D
var eyes: Array[MeshInstance3D] = []
var mouth: MeshInstance3D
var bob := 0.0
var blink := 0.0
var t := 0.0

func _ready():
    root3d = Node3D.new()
    add_child(root3d)
    _setup_environment()
    _build_alya()
    _build_ui()

func _setup_environment():
    var env = WorldEnvironment.new()
    var e = Environment.new()
    e.background_mode = Environment.BG_COLOR
    e.background_color = Color("#090c15")
    e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    e.ambient_light_color = Color("#9bb7ff")
    e.ambient_light_energy = 0.65
    env.environment = e
    add_child(env)

    var key = DirectionalLight3D.new()
    key.rotation_degrees = Vector3(-25, -25, 0)
    key.light_energy = 1.2
    key.shadow_enabled = true
    add_child(key)

    var fill = OmniLight3D.new()
    fill.position = Vector3(-2, 2.5, 3)
    fill.light_color = Color("#9bb7ff")
    fill.omni_range = 8
    fill.light_energy = 3.0
    add_child(fill)

    var camera = Camera3D.new()
    camera.position = Vector3(0, 1.45, 5.4)
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
    character.position = Vector3(0, -0.15, 0)
    root3d.add_child(character)

    var skin = mat(Color("#f2d8d8"))
    var hair = mat(Color("#c2cad8"))
    var blue = mat(Color("#5d8cff"), 0.35)
    var dark = mat(Color("#1a2135"))
    var hoodie = mat(Color("#34446d"))
    var white = mat(Color("#f4f7ff"))

    # body / hoodie
    cyl(character, Vector3(0,0.85,0), Vector3(0.72,0.78,0.45), hoodie)
    sphere(character, Vector3(0,1.45,0), Vector3(0.72,0.78,0.68), skin)
    head = character.get_child(character.get_child_count()-1)

    # hair cap + side locks
    sphere(character, Vector3(0,1.63,-0.02), Vector3(0.79,0.72,0.73), hair)
    sphere(character, Vector3(-0.66,1.35,0), Vector3(0.20,0.65,0.22), hair)
    sphere(character, Vector3(0.66,1.35,0), Vector3(0.20,0.65,0.22), hair)

    # eyes
    eyes.append(sphere(character, Vector3(-0.27,1.48,-0.66), Vector3(0.12,0.19,0.06), blue))
    eyes.append(sphere(character, Vector3(0.27,1.48,-0.66), Vector3(0.12,0.19,0.06), blue))
    mouth = sphere(character, Vector3(0,1.25,-0.69), Vector3(0.12,0.035,0.025), dark)

    # hoodie strings
    cyl(character, Vector3(-0.12,1.05,-0.48), Vector3(0.025,0.32,0.025), white)
    cyl(character, Vector3(0.12,1.05,-0.48), Vector3(0.025,0.32,0.025), white)

    # simple arms
    var left = cyl(character, Vector3(-0.72,0.75,0), Vector3(0.20,0.62,0.20), hoodie)
    left.rotation_degrees.z = -18
    var right = cyl(character, Vector3(0.72,0.75,0), Vector3(0.20,0.62,0.20), hoodie)
    right.rotation_degrees.z = 18

    # floating name plate
    var label = Label3D.new()
    label.text = "ALYA"
    label.position = Vector3(0,2.55,0)
    label.font_size = 42
    label.modulate = Color("#dbe6ff")
    label.outline_size = 8
    character.add_child(label)

func _build_ui():
    var layer = CanvasLayer.new()
    add_child(layer)
    var panel = ColorRect.new()
    panel.position = Vector2(16,16)
    panel.size = Vector2(328,54)
    panel.color = Color(0.05,0.07,0.12,0.88)
    layer.add_child(panel)

    var title = Label.new()
    title.text = "ALYA  •  3D PROTOTYPE"
    title.position = Vector2(30,28)
    title.add_theme_font_size_override("font_size",18)
    title.modulate = Color("#dbe6ff")
    layer.add_child(title)

    var hint = Label.new()
    hint.text = "3D body • expressions • idle animation"
    hint.position = Vector2(30,58)
    hint.add_theme_font_size_override("font_size",11)
    hint.modulate = Color("#9aa7c5")
    layer.add_child(hint)

func _process(delta):
    t += delta
    bob = sin(t * 1.8) * 0.035
    if character:
        character.position.y = -0.15 + bob
        character.rotation.y = sin(t * 0.55) * 0.07

    # subtle eye blink animation
    blink += delta
    if blink > 3.0:
        var close := clamp((blink - 3.0) * 10.0, 0.0, 1.0)
        for e in eyes:
            e.scale.y = lerp(0.19, 0.025, close)
        if blink > 3.18:
            blink = 0.0
    else:
        for e in eyes:
            e.scale.y = 0.19
