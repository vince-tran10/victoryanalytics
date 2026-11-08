# Load Rejuvenation's definition files (plain Ruby literals) and dump them as JSON.
# usage: ruby to_json.rb <definitions dir> <out dir>
require 'json'
# stand-ins for game constants (PBStats::ATTACK etc.) -> the string "PBStats::ATTACK"
class Object
  def self.const_missing(name)
    m = Module.new
    m.define_singleton_method(:const_missing) { |c| "#{name}::#{c}" }
    const_set(name, m)
  end
end
src, out, scripts = ARGV
Rejuv = true unless defined?(Rejuv)
# the game's real constants (PBStats, PBStuff, PBFields move lists) so field files resolve exactly as in game
if scripts
  eval(File.read(File.join(scripts, 'PBConstants.rb'), encoding: 'UTF-8'), TOPLEVEL_BINDING)
  stuff = File.read(File.join(scripts, 'PBStuff.rb'), encoding: 'UTF-8')
  # PBStuff.rb as a whole needs the running game; take only the pieces the field file uses
  eval(stuff[/^class PBFields\b.*?^end/m], TOPLEVEL_BINDING)
  eval("class PBStuff\n" + stuff[/^  TERRAINMOVE = .*?$/] + "\nend", TOPLEVEL_BINDING)
end
def conv(x)
  case x
  when Hash then x.map { |k, v| [k.is_a?(Symbol) ? k.to_s : k.to_s, conv(v)] }.to_h
  when Array then x.map { |v| conv(v) }
  when Symbol then x.to_s
  when Range then [x.first, x.last]
  when Proc then '<proc>'
  else x
  end
end
{ 'trainertext' => :TEAMARRAY, 'bosstext' => :BOSSINFOHASH, 'fieldtext' => :FIELDEFFECTS, 'montext' => :MONHASH,
  'movetext' => :MOVEHASH, 'abiltext' => :ABILHASH, 'itemtext' => :ITEMHASH, 'typetext' => :TYPEHASH }.each do |f, const|
  begin
    eval(File.read(File.join(src, "#{f}.rb"), encoding: 'UTF-8'), TOPLEVEL_BINDING)
    data = Object.const_get(const)
    File.write(File.join(out, "#{f}.json"), JSON.generate(conv(data)))
    puts "#{f}: #{data.size} entries"
  rescue Exception => e
    puts "#{f}: FAILED #{e.class}: #{e.message[0, 200]}"
  end
end
