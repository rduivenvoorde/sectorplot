-- base64, hex, escape
select block, length(zoneradii), encode(zoneradii, 'hex'), zoneradii from npp limit 1
