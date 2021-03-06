#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys
import shape

def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-n", "--noupgrade", dest="doupgrade",
                    action="store_false", default=True, help="dry run")

  # all required
  parser.add_option("-f", "--fleet", dest="fleetstr",
                    action="store", type="string", help="fleet type")
  parser.add_option("-o", "--owner", dest="owner",
                    type="string", help="owner to assault")
  parser.add_option("-s", "--source_route", dest="source",
                    type="string", help="route enclosing source")
  parser.add_option("-d", "--dest_route", dest="dest",
                    type="string", help="route enclosing dest")

  (options, args) = parser.parse_args()

  if options.dest == None or options.owner == None or options.fleetstr == None:
    print "not enough arguments"
    parser.print_help()
    sys.exit(1)

  print "options " + str(options)

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  g.load_routes()
  try:
    dest_route = g.find_route(options.dest)
    dest_shape = shape.Polygon(*(dest_route.points))
  except:
    print "could't find dest route"
    sys.exit(1)

  source_shape = None
  if options.source:
    try:
      source_route = g.find_route(options.source)
      source_shape = shape.Polygon(*(source_route.points))
    except:
      print "could't find source route"
      sys.exit(1)

  #print source_shape
  #print dest_shape

  Assault(g, options.doupgrade, options.fleetstr, source_shape, dest_shape, options.owner)

def MakePoints(location):
  points = (location[0] - .2, location[1]),(location[0] + .2, location[1])
  return points

def Assault(g, doupgrade, fleetstr, source, dest, owner):
  f = game.ParseFleet(fleetstr)
  print f

  built = 0

  # find a list of potential fleet builders
  print "looking for fleet builders..."
  total_fleets = 0
  fleet_builders = []
  for p in g.planets:
    if source == None or source.inside(p.location):
      p.load()
      count = p.how_many_can_build(f)
      if count > 0:
        print "planet " + str(p) + " can build " + str(count) + " fleets"
        p.distance_to_target = dest.distance(p.location)
        fleet_builders.append(p)
        total_fleets += count

  # sort fleet builders by distance to target
  fleet_builders = sorted(fleet_builders, key=lambda planet: planet.distance_to_target)

  print "found " + str(len(fleet_builders)) + " fleet building planets capable of building " + str(total_fleets) + " fleets"

  # load the sectors around the target point
  print "looking for owned planets at target location..."
  sect = g.load_sectors(dest.bounding_box())
  #print sect
  targets = []
  for p in sect["planets"]["owned"]:
    print p
    if p.owner == owner:
      routename = "assault%s" %(str(p.planetid))
      r = g.find_route(routename)
      if r == None:
        targets.append(p)

  print "found " + str(len(targets)) + " target planets"

  g.load_fleet_cache()
  build = 0
  if len(targets) > 0:
    print "building assault fleets"
    done = False
    for p in fleet_builders:
      if done:
        break

      # for this builder, find the closest unowned planets
      for t in targets:
        t.distance_to_target = game.distance_between(p.location, t.location)
      targets = sorted(targets, key=lambda planet: planet.distance_to_target)

      count = p.how_many_can_build(f);

      print "planet " + str(p) + " can build " + str(count) + " fleets"
      while not done and count > 0 and p.can_build(f):
        t = targets[0]
        print "looking to build to " + str(t) + " distance: " + str(t.distance_to_target)
        if doupgrade:
          fleet = p.build_fleet(f)
          if fleet:
            #fleet.move_to_planet(t)
            routename = "assault%s" %(str(t.planetid))
            r = g.find_route(routename)
            if r == None:
              print "building route"
              points = MakePoints(t.location)
              #print points

              r = g.create_route("assault%s" % (str(t.planetid)), True, points);
              #print r

            print "moving fleet to new route"
            if fleet.move_to_route(r) == False:
              print "error moving fleet"
          else:
            print " failed to build fleet"
            count = 0
            break

        # cull this target from the list
        targets.remove(t)
        built += 1
        count -= 1
        if len(targets) == 0:
          done = True

  if built > 0:
    if doupgrade:
      print "built %d fleets" % built
    else:
      print "would have built %d fleets" % built

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
