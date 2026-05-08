package com.petfinect.api.web;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.petfinect.api.domain.Family;
import com.petfinect.api.security.JwtAuthenticationFilter.AuthenticatedUser;
import com.petfinect.api.service.FamilyAccess;
import com.petfinect.api.service.FamilyService;
import com.petfinect.api.web.dto.CreateFamilyResponse;
import com.petfinect.api.web.dto.FamilyCreateRequest;
import com.petfinect.api.web.dto.FamilyDetail;
import com.petfinect.api.web.dto.FamilySummary;
import com.petfinect.api.web.dto.InviteRequest;
import com.petfinect.api.web.dto.InviteResponse;
import com.petfinect.api.web.dto.JoinRequest;
import com.petfinect.api.web.dto.JoinResponse;
import com.petfinect.api.web.dto.MemberDetailResponse;
import com.petfinect.api.web.exception.ApiException;

import jakarta.validation.Valid;

/**
 * Family 라우트 — Python {@code apps/api/app/api/v1/families.py} 와 contract 동일.
 *
 * <h3>엔드포인트</h3>
 * <ul>
 *   <li>POST /v1/families — 생성 + 본인 owner</li>
 *   <li>GET /v1/families — 내 가족 목록</li>
 *   <li>POST /v1/families/{id}/invite — 초대 코드 발급 (owner)</li>
 *   <li>POST /v1/families/join — 코드로 가입</li>
 *   <li>GET /v1/families/{id}/members — 멤버 목록 (member 이상)</li>
 * </ul>
 *
 * <h3>Path 파라미터 → UUID 파싱</h3>
 * <ul>
 *   <li>{@code @PathVariable UUID familyId} — Spring 이 String → UUID 변환을 자동.
 *       parse 실패 시 400. 하지만 Python 정책은 "모르는 family ID = 404" 라
 *       {@link #parseUuidOr404}로 catch 후 404 변환.</li>
 * </ul>
 */
@RestController
@RequestMapping("/v1/families")
public class FamilyController {

	private final FamilyService familyService;
	private final FamilyAccess familyAccess;

	public FamilyController(FamilyService familyService, FamilyAccess familyAccess) {
		this.familyService = familyService;
		this.familyAccess = familyAccess;
	}

	@PostMapping("")
	public CreateFamilyResponse create(
		@Valid @RequestBody FamilyCreateRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		Family fam = familyService.createWithOwner(principal.claims().sub(), req.name());
		return new CreateFamilyResponse(
			new FamilyDetail(fam.getId(), fam.getName()),
			Map.of("role", "owner")
		);
	}

	@GetMapping("")
	public List<FamilySummary> list(@AuthenticationPrincipal AuthenticatedUser principal) {
		return familyService.listMyFamilies(principal.claims().sub()).stream()
			.map(item -> new FamilySummary(item.id(), item.name(), item.role(), item.memberCount()))
			.toList();
	}

	@PostMapping("/{family_id}/invite")
	public InviteResponse invite(
		@PathVariable("family_id") String familyId,
		@RequestBody(required = false) InviteRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		UUID fid = parseUuidOr404(familyId);
		familyAccess.requireOwner(fid, principal.claims());
		int ttlHours = (req != null && req.ttlHours() != null) ? req.ttlHours() : 72;
		FamilyService.InviteResult result = familyService.issueInvite(fid, ttlHours);
		return new InviteResponse(result.inviteCode(), result.expiresAt());
	}

	@PostMapping("/join")
	public JoinResponse join(
		@Valid @RequestBody JoinRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		Family fam = familyService.joinByCode(principal.claims().sub(), req.inviteCode());
		return new JoinResponse(new FamilyDetail(fam.getId(), fam.getName()), "member");
	}

	@GetMapping("/{family_id}/members")
	public List<MemberDetailResponse> members(
		@PathVariable("family_id") String familyId,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		UUID fid = parseUuidOr404(familyId);
		familyAccess.requireMember(fid, principal.claims());
		return familyService.listMembers(fid).stream()
			.map(m -> new MemberDetailResponse(m.userId(), m.name(), m.role(), m.joinedAt()))
			.toList();
	}

	private UUID parseUuidOr404(String s) {
		try {
			return UUID.fromString(s);
		} catch (IllegalArgumentException exc) {
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "family not found");
		}
	}
}
