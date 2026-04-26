graph LR                                                               
      subgraph INPUTS["Input Scripts"]
          face["face_detect.py\nwebcam → face events"]                   
          audio["audio.py\nmic → speech / startle"]
          sim["simulate.py\nsynthetic sensor sim"]                       
          sched["time_scheduler.py\nday-curve pressure"]                 
          send["send.py · states.py\none-shot · scenarios · REPL"]       
      end
      subgraph RELAY["server.py · WebSocket Relay"]
          relay(["broadcast\nall ↔ all"])
      end

      subgraph BROWSER["Browser · index.html"]
          direction TB

          subgraph ENGINE["Behavior Engine"]
              comp["Compositor\nattn layer + affect layer\n17 behaviors"]
              drive["Drive System\npressure · rule engine · task queue"]
          end

          subgraph MOTION["Motion Planning"]
              saccade["GazeSaccade\nbézier arcs · anticipation ·

  overshoot"]
              head["Head Controller\n3-phase motion profile"]
          end
          subgraph WORLD["World Model"]
              poi["9 POIs\nfamiliarity · attention · draggable"]
              smem["Spatial Memory\n0.5 m grid · novelty bias"]
              battery["Battery\ndrain · charge · sleep schedule"]
          end

          subgraph MOB["Mobility"]
              mob["State Machine\nhold → wander → approach → scan →

  charging"]
              diff["Differential Drive\nv_L · v_R · arc turns"]
              avoid["Potential Fields\nobstacle avoidance"]
          end
          subgraph RENDER["Rendering"]
              eye["Eye Canvas · 2D"]
              body["Three.js Scene\nbody · head · wheels"]
              cams["5 Cameras\nFace · POV · Ceiling · Travel ·

  Perspective"]
              hmap["Floor Heatmap\nvisited cells · yellow → red"]
          end
          drive -->|"selects behavior"| comp
          comp -->|"gaze target"| saccade
          saccade --> eye
          comp --> head
          head --> body
          poi -->|"wander targets"| mob
          smem -->|"novelty score"| mob
          battery -->|"low → return home"| mob
          mob --> diff
          diff --> body
          avoid --> mob
      end

      subgraph RECORD["Recording / Playback"]
          rec["recorder.py\nJSONL timestamped sessions"]
          rep["replay.py\nplayback at original cadence"]
      end

      INPUTS -->|"WebSocket commands"| relay
      relay -->|"inbound commands"| BROWSER
      BROWSER -->|"full state · 20 Hz"| relay
      relay --> rec
      rep -->|"JSONL replay"| relay


