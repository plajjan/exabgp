# encoding: utf-8
"""
path.py

Created by Thomas Mangin on 2014-06-27.
Copyright (c) 2009-2015 Exa Networks. All rights reserved.
"""

from exabgp.protocol.ip import IP
from exabgp.protocol.ip import NoNextHop
from exabgp.protocol.family import AFI
from exabgp.protocol.family import SAFI
from exabgp.bgp.message.update.nlri.nlri import NLRI
from exabgp.bgp.message.update.nlri.cidr import CIDR
from exabgp.bgp.message.update.nlri.qualifier import PathInfo


@NLRI.register(AFI.ipv4,SAFI.unicast)
@NLRI.register(AFI.ipv6,SAFI.unicast)
@NLRI.register(AFI.ipv4,SAFI.multicast)
@NLRI.register(AFI.ipv6,SAFI.multicast)
class INET (CIDR,NLRI):
	__slots__ = ['path_info','nexthop','action']

	def __init__ (self, afi, safi, packed, mask, nexthop, action):
		self.path_info = PathInfo.NOPATH
		self.nexthop = IP.unpack(nexthop) if nexthop else NoNextHop
		NLRI.__init__(self,afi,safi)
		CIDR.__init__(self,packed,mask)
		self.action = action

	def prefix (self):
		return "%s/%s%s" % (CIDR.top(self),self.mask,str(self.path_info) if self.path_info is not PathInfo.NOPATH else '')

	def extensive (self):
		return "%s/%s%s next-hop %s" % (self.top(),self.mask,str(self.path_info) if self.path_info is not PathInfo.NOPATH else '',self.nexthop)

	def pack (self, negotiated):
		# from exabgp.bgp.message.open.capability import Negotiated
		# assert type(negotiated) is Negotiated
		if negotiated.addpath.send(self.afi,self.safi):
			return self.path_info.pack() + self.cidr()
		return self.cidr()

	def json (self):
		return '"%s/%s": { %s }' % (CIDR.top(self),self.mask,self.path_info.json())

	def index (self):
		if self.path_info is PathInfo.NOPATH:
			return 'path-nopath' + self.path_info.pack() + self.cidr()
		return 'path-packed' + self.path_info.pack() + self.cidr()

	def __len__ (self):
		return CIDR.__len__(self) + len(self.path_info)

	def __repr__ (self):
		nexthop = ' next-hop %s' % self.nexthop if self.nexthop else ''
		return "%s%s" % (self.prefix(),nexthop)

	@classmethod
	def unpack (cls, afi, safi, data, addpath, nexthop, action):
		labels,rd,path_identifier,mask,size,prefix,left = NLRI._nlri(afi,safi,data,action,addpath)
		nlri = cls(afi,safi,prefix,mask,nexthop,action)
		if path_identifier:
			nlri.path_info = PathInfo(None,None,path_identifier)
		return len(data) - len(left),nlri
